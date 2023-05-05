'''
Created on 5 mai 2023


'''
import base64
import json
import os
from pathlib import Path

from django.conf import settings
import dramatiq
import threading
import datetime
from django.core.files.base import File, ContentFile
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# TESTs
# - calcul quand step_reference n'existe pas
# - suppression de l'ancien fichier .json
# - calcul quand step_reference existe déjà => on écrit
# - vérifier que le json est sauvegardé
# - erreur dans la détection
# - pas de calcul => timeout

@dramatiq.actor(store_results=True, max_age=10000)
def detect_remote(processor_name, imageb64, image_name, resize_factor):
    """
    @param processor_name: name of the processor to use
    @param imageb64: image transmitted as a Base 64 string
    @param image_name: name of the file
    @param resize_factor: factor to apply to picture, in case it's small (for example)
    """
    # if we are here, it means we are in unit tests, so content may be json string (the reply)
    # expected format:
    # {"field": {
    #     'error': 'a possible error',
    #     'version': 'model_version',
    #     'image': <base64 encoded image file with bounding boxes>
    #     'data': [ObjectBox1, ObjectBox2]
    #   },
    # "text": {
    #       "text1": {box}...
    #   }
    # }
    try:
        data = json.loads(base64.b64decode(imageb64))
        return data['field']
    except Exception as e:

        return {'error': str(e)}


@dramatiq.actor(store_results=True, max_age=10000)
def detect_text_remote(imageb64, image_name):
    """
    Detect text on picture
    @param imageb64: image transmitted as a Base 64 string
    @param image_name: name of the file
    """
    # if we are here, it means we are in unit tests, so content may be json string (the reply)
    # expected format:
    # {"field": {
    #     'error': 'a possible error',
    #     'version': 'model_version',
    #     'image': <base64 encoded image file with bounding boxes>
    #     'data': [ObjectBox1, ObjectBox2]
    #   },
    # "text": {
    #       "text1": {box}...
    #   }
    # }
    try:
        reply = json.loads(base64.b64decode(imageb64))['text']
        return reply
    except:
        return {'error': None}


class FieldDetectorThread(threading.Thread):
    
    def __init__(self, step_reference):
        """
        Init computer thread
        @param step_reference: the step reference that will be computed
        """
        super().__init__()
        self.step_reference = step_reference
    
    def run(self):
        file_path = Path(self.step_reference.image.name)
        
        if self.step_reference.field_detection_data and self.step_reference.field_detection_data.path:
            old_path = self.step_reference.field_detection_data.path
        else:
            old_path = None
        
        with self.step_reference.image.file as image_file:
            detection_data = FieldDetector().detect(image_file.read(), file_path.name, 'field_processor', 1.0)
        
            # computing OK, record result
            if not detection_data['error']:
                self.step_reference.field_detection_date = timezone.now()
                self.step_reference.field_detection_version = detection_data.get('version', '')
                self.step_reference.field_detection_data.save(file_path.with_suffix('.json').name, ContentFile(json.dumps(detection_data)))
                self.step_reference.save()
                
                # remove old json file
                try:
                    os.remove(old_path)
                except (FileNotFoundError, TypeError, PermissionError) as e:
                    pass
        

class FieldDetector(object):

        
    def detect(self, image:bytes, file_name:str, processor_name:str, resize_factor:float):
        """
        Returns the result of field detection process
        
        detection_data = {
                <file_name>: {
                    'fields': detection_img_data, 
                    'labels': list(detection_text_data)
                },
                'error': detection_img_data['error'],
                'version': detection_img_data['version']
            }
        
        @param image: the image to detect fields in  (bytes-like object)
        @param file_name: the name of the stored file
        @param processor_name: name of the processor to use ('error_processor' or 'field_processor')
        @param resize_factor: factor to apply to image for detection (e.g: 1.0)
        """
        
        logger.info(f"detecting fields for file {file_name}")
        b64_image = base64.b64encode(image).decode('utf-8')
        message_fields = detect_remote.send(processor_name, b64_image, file_name, resize_factor)
        message_text = detect_text_remote.send(b64_image, file_name)

        detection_img_data =  message_fields.get_result(block=True)
        detection_text_data =  message_text.get_result(block=True)
        logger.info(f"finished detecting fields for file {file_name}")
        return self.merge_detection_data(file_name, detection_text_data, detection_img_data)
    
    
    def merge_detection_data(self, file_name, detection_text_data, detection_img_data):
        """
        @param detection_img_data: data collected during detection by Yolo algorithm. Format is {'error': <some_error>, 'data': [...], 'image': <base64 image>}
        """
        if 'data' not in detection_img_data:
            return {'error': detection_img_data['error']}

        # process text on image to match detected boxes with labels
        self.correlate_text_and_fields(detection_text_data, detection_img_data['data'])

        # create output data
        detection_data = {
                file_name: {
                    'fields': detection_img_data['data'], 
                    'labels': list(detection_text_data.values())
                },
                'error': detection_img_data['error'],
                'version': detection_img_data['version']
            }

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'detect'), exist_ok=True)

        # store the file locally for use with debug API
        file_path = Path(file_name)
        if 'image' in detection_img_data and detection_img_data['image']:
            Path(settings.MEDIA_ROOT, 'detect', file_path.with_suffix(file_path.suffix)).write_bytes(base64.b64decode(detection_img_data['image'].encode('utf-8')))

        Path(settings.MEDIA_ROOT, 'detect', file_path.with_suffix('.json')).write_text(json.dumps(detection_data), 'utf-8')

            
        return detection_data
    
    def correlate_text_and_fields(self, text_boxes, field_boxes):
        """
        Try to match a box discovered by tesseract and a box discovered by field recognition, when this box has a label
        """
        
        for name, text_box in text_boxes.items():
            
            x_text_box_center = (text_box['right'] - text_box['left']) / 2 + text_box['left']
            y_text_box_center = (text_box['bottom'] - text_box['top']) / 2 + text_box['top']
            
            for field_box in field_boxes:
                
                if (field_box['left'] < x_text_box_center < field_box['right']
                        and field_box['top'] < y_text_box_center < field_box['bottom']
                    # set the text for error_fields inconditionnaly, as we try to get the error message
                    # for other fields (button, text fields, ...), we try to match only if field has a label
                    and (field_box['with_label'] or field_box['class_name'] == 'error_field')):
                    field_box['text'] = text_box['text']
                    break