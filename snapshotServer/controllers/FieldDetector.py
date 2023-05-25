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
from dramatiq.results.errors import ResultTimeout
import time

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
    data = base64.b64decode(imageb64)
    
    if data == b'exception:ResultTimeout':
        raise ResultTimeout("timeout")
    elif data == b'exception:ConnectionError':
        raise ConnectionError("")
        
    try:
        data = json.loads(data)
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
    data = base64.b64decode(imageb64)
    
    if data == b'exception:ResultTimeout':
        raise ResultTimeout("timeout")
    elif data == b'exception:ConnectionError':
        raise ConnectionError("")
    try:
        data = json.loads(data)
        return data['text']
    except Exception as e:
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
                self.step_reference.save()
                self.step_reference.field_detection_data.save(file_path.with_suffix('.json').name, ContentFile(json.dumps(detection_data)))
                
                
                if old_path:
                    try:
                        # remove old json file in 'reference' folder
                        Path(old_path).unlink(True)
                        
                        # remove previous files in 'detect' folder
                        Path(settings.MEDIA_ROOT, 'detect', Path(old_path).name).unlink(True)
                        Path(settings.MEDIA_ROOT, 'detect', Path(old_path).with_suffix('.jpg').name).unlink(True) # reference pictures are in jpg because video recording uses MJEPG codec
                        Path(settings.MEDIA_ROOT, 'detect', Path(old_path).with_suffix('.png').name).unlink(True) # reference pictures for tests are in png
                    except (PermissionError) as e:
                        pass

class FieldDetector(object):
    
    last_clean = datetime.datetime.today()
    clean_lock = threading.Lock()
    DELETE_AFTER = 60 * 60 * 24 * 30
    CLEAN_EVERY_SECONDS = 60 * 60 * 24

    def clean(self):
        """
        clean detect folder for files older than 30 days
        Do only every day
        """
        
        with FieldDetector.clean_lock:
            if (datetime.datetime.today() - FieldDetector.last_clean).seconds < FieldDetector.CLEAN_EVERY_SECONDS:
                return
            
        for f in Path(settings.MEDIA_ROOT, 'detect').iterdir():
        
            if f.is_file() and time.time() - f.stat().st_mtime > FieldDetector.DELETE_AFTER:
                try:
                    f.unlink(True)
                except Exception as e:
                    logging.warn("cannot delete file: " + f)
                    
        with FieldDetector.clean_lock:
            FieldDetector.last_clean = datetime.datetime.today()
        
    def detect(self, image:bytes, file_name:str, processor_name:str, resize_factor:float):
        """
        Returns the result of field detection process
        
        detection_data = {
                'fields': detection_img_data, 
                'labels': list(detection_text_data),
                'fileName': <file_name>,
                'error': detection_img_data['error'],
                'version': detection_img_data['version']
            }
        
        @param image: the image to detect fields in  (bytes-like object)
        @param file_name: the name of the stored file
        @param processor_name: name of the processor to use ('error_processor' or 'field_processor')
        @param resize_factor: factor to apply to image for detection (e.g: 1.0)
        """
        self.clean()
        
        if settings.FIELD_DETECTOR_ENABLED != 'True':
            return {'error': 'Field detector disabled'}
        
        logger.info(f"detecting fields for file {file_name}")
        b64_image = base64.b64encode(image).decode('utf-8')
        message_fields = detect_remote.send(processor_name, b64_image, file_name, resize_factor)
        message_text = detect_text_remote.send(b64_image, file_name)

        try:
            detection_img_data =  message_fields.get_result(block=True)
            detection_text_data =  message_text.get_result(block=True)
            logger.info(f"finished detecting fields for file {file_name}")
            return self.merge_detection_data(file_name, detection_text_data, detection_img_data)
        except ResultTimeout as e:
            return {'error': 'Timeout waiting for computation'}
        except ConnectionError as e:
            return {'error': 'No redis server found'}
        except Exception as e:
            return {'error': 'Compute error ' + str(e)}
    
    
    def merge_detection_data(self, file_name:str, detection_text_data:dict, detection_img_data:dict):
        """
        @param file_name: name of the picture file
        @param detection_text_data: data collected with tesseract. Format is {'text1': [
            {
                "top": 3,
                "left": 16,
                "width": 72,
                "height": 16,
                "text": "text1",
                "right": 88,
                "bottom": 19
            },
        @param detection_img_data: data collected during detection by Yolo algorithm. Format is {'error': <some_error>, 'data': [...], 'image': <base64 image>}
        
        """
        if 'data' not in detection_img_data:
            return {'error': detection_img_data['error']}

        # process text on image to match detected boxes with labels
        self.correlate_text_and_fields(detection_text_data, detection_img_data['data'])

        # create output data
        detection_data = {
                'fields': detection_img_data['data'], 
                'labels': list(detection_text_data.values()),
                'fileName': file_name,
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
    
    def correlate_text_and_fields(self, text_boxes:dict, field_boxes:list):
        """
        Try to match a box discovered by tesseract and a box discovered by field recognition, when this box has a label
        """
        
        for name, text_box in text_boxes.items():
            
            x_text_box_center = (text_box['right'] - text_box['left']) / 2 + text_box['left']
            y_text_box_center = (text_box['bottom'] - text_box['top']) / 2 + text_box['top']
            
            for field_box in field_boxes:
                
                if (field_box['left'] < x_text_box_center < field_box['right']
                        and field_box['top'] < y_text_box_center < field_box['bottom']
                    # set the text for error_fields unconditionnaly, as we try to get the error message
                    # for other fields (button, text fields, ...), we try to match only if field has a label
                    and (field_box['with_label'] or field_box['class_name'] == 'error_field')):
                    field_box['text'] = text_box['text']
                    break