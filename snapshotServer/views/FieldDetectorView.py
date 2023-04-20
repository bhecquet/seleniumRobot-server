'''
Created on 18 avr. 2023

@author: S047432
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.http.response import HttpResponse
from snapshotServer.forms import ImageForFieldDetectionForm

import base64
import dramatiq
import os
from pathlib import Path
import json
import logging
import unidecode

from snapshotServer.models import Application, Snapshot

logger = logging.getLogger(__name__)

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



class FieldDetectorView(APIView):

    queryset = Snapshot.objects.filter(pk=1) # for rights in tests
    
    def get(self, request, format=None):
        """
        Method that returns the debug information of a previously 'detected' image
        :param request:
        :param format:
        :return:
        """
        detect_folder_path = Path(settings.MEDIA_ROOT, 'detect')

        image_name = request.GET['image']
        if image_name is None:
            Response(status=status.HTTP_400_BAD_REQUEST, data="'image' parameter is mandatory")
        elif image_name in os.listdir(detect_folder_path):
            return HttpResponse((detect_folder_path / image_name).read_bytes(), content_type='image/png');
        elif unidecode.unidecode(image_name.replace(' ', '_')) in os.listdir(detect_folder_path):
            return HttpResponse((detect_folder_path / unidecode.unidecode(image_name.replace(' ', '_'))).read_bytes(), content_type='image/png')
        else:
            Response(status=status.HTTP_404_NOT_FOUND, data="image '%s' not found" % image_name)

    def post(self, request, format=None):
        """
        Method to send an image and get detection data (POST)
        
        to test: curl -F "image=@D:\Dev\yolo\yolov3\dataset_generated_small\out-7.jpg"   -F "task=field" http://127.0.0.1:5000/detect/
        """
        form = ImageForFieldDetectionForm(request.POST, request.FILES)

        if form.is_valid():
            saved_file = form.cleaned_data['image']
            processor_name = form.cleaned_data['task'] + '_processor'

            b64_image = base64.b64encode(saved_file.file.read()).decode('utf-8')
            message_fields = detect_remote.send(processor_name, b64_image, saved_file.name, form.cleaned_data['resizeFactor'])
            message_text = detect_text_remote.send(b64_image, saved_file.name)

            detection_img_data =  message_fields.get_result(block=True)
            detection_text_data =  message_text.get_result(block=True)
            detection_data = self.merge_detection_data(saved_file.name, detection_text_data, detection_img_data)

            return self.finalize_detection(detection_data)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=str(form.errors))

    
    def finalize_detection(self, detection_data):
        """
        Send a reply depending on detection data
        delete locally recorded file
        
        @param detection_data: data collected through detection process
        @param saved_file: file recorded locally
        """
        
        if not detection_data:
            return Response({'error': "Error in detection"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif detection_data['error']:
            return Response(detection_data['error'], status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(detection_data, status=status.HTTP_200_OK)


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



