'''
Created on 18 avr. 2023

@author: S047432
'''
import base64
import json
import logging
import os
from pathlib import Path

from django.conf import settings
from django.http.response import HttpResponse
import dramatiq
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import unidecode

from snapshotServer.controllers.FieldDetector import FieldDetector
from snapshotServer.forms import ImageForFieldDetectionForm
from snapshotServer.models import Application, Snapshot


logger = logging.getLogger(__name__)

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
        additionaly, redis serveur must be available and configured in settings.py
        DRAMATIQ_BROKER['OPTIONS']['url'] = 'redis://server.com:6379/0'
        DRAMATIQ_RESULT_BACKEND['BACKEND_OPTIONS']['url'] = 'redis://server.com:6379'
        
        An image-field-detector is also started to handle computing
        """
        form = ImageForFieldDetectionForm(request.POST, request.FILES)

        if form.is_valid():
            saved_file = form.cleaned_data['image']
            processor_name = form.cleaned_data['task'] + '_processor'
            
            detection_data = FieldDetector().detect(saved_file.file.read(), saved_file.name, processor_name, form.cleaned_data['resizeFactor'])
#
            # b64_image = base64.b64encode(saved_file.file.read()).decode('utf-8')
            # message_fields = detect_remote.send(processor_name, b64_image, saved_file.name, form.cleaned_data['resizeFactor'])
            # message_text = detect_text_remote.send(b64_image, saved_file.name)
            #
            # detection_img_data =  message_fields.get_result(block=True)
            # detection_text_data =  message_text.get_result(block=True)
            # detection_data = self.merge_detection_data(saved_file.name, detection_text_data, detection_img_data)

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





