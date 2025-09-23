
import logging
import os
from pathlib import Path

from django.conf import settings
from django.http.response import HttpResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, CreateAPIView

from snapshotServer.controllers.FieldDetector import FieldDetector, \
    FieldDetectorThread
from snapshotServer.forms import ImageForFieldDetectionForm,\
    DataForFieldDetectionForm
from snapshotServer.models import Snapshot, StepReference, \
    StepResult
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording


logger = logging.getLogger(__name__)

class FieldDetectorPermission(ApplicationSpecificPermissionsResultRecording):
    
    def get_object_application(self, obj):
        return ''
        
    def get_application(self, request, view):
        return ''

class FieldDetectorView(RetrieveAPIView, CreateAPIView):
    """
    This view requires Snapshot model permissions
    """

    queryset = Snapshot.objects.filter(pk=1) # for rights in tests
    permission_classes = [FieldDetectorPermission]
    
    def get(self, request):
        """
        Method that returns the debug information of a previously 'detected' image
        URL parameters MUST contains either:
        - "image": the name of the file previously submitted through POST request
          "output": "json" (default) or "image"
            e.g: http://127.0.0.1:8000/detect/?image=<image_name>"
        - "stepResultId": id of the test step result so that we can find the associated application / version / test case / environment values
          "version": version of the model used to compute fields  
          "output": "json" (default) or "image"
            e.g: http://127.0.0.1:8002/snapshot/detect/?stepResultId=90&version=afcc45
        
        In both case, it returns a JSON 
        {
    "<image_name>": {
        "fields": [
            {
                "class_id": 2,
                "top": 216,
                "bottom": 239,
                "left": 277,
                "right": 342,
                "class_name": "button",
                "text": null,
                "related_field": null,
                "with_label": false,
                "width": 65,
                "height": 23
            },
        [...]
        ],
        "labels": [
            {
                "top": 3,
                "left": 16,
                "width": 72,
                "height": 16,
                "text": "Join Us",
                "right": 88,
                "bottom": 19
            },
        [...]
        ]
    },
    "error": null,
    "version": "afcc45"
}
        
        :param request
        :return:
        """
        form = DataForFieldDetectionForm(request.GET)

        if form.is_valid():
            if form.cleaned_data['image']:
                return self._get_fields_from_image_name(form)
            elif form.cleaned_data['stepResultId']:
                return self._get_fields_from_step_result_id(form) 
            
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=str(form.errors))
        
    def _get_fields_from_image_name(self, form):
        detect_folder_path = Path(settings.MEDIA_ROOT, 'detect')
        if form.cleaned_data['image'] in os.listdir(detect_folder_path):
            if form.cleaned_data['output'] == 'image':
                return HttpResponse((detect_folder_path / form.cleaned_data['image']).read_bytes(), content_type='image/png', status=200)
            else:
                return HttpResponse((detect_folder_path / form.cleaned_data['image']).with_suffix('.json').read_text(), content_type='application/json', status=200)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND, data="image '%s' not found" % form.cleaned_data['image'])
        
    def _get_fields_from_step_result_id(self, form):
        detect_folder_path = Path(settings.MEDIA_ROOT, 'detect')
        
        step_result = StepResult.objects.get(id=form.cleaned_data['stepResultId'])
        step_reference = StepReference.objects.filter(testCase=step_result.testCase.testCase, 
                                         version=step_result.testCase.session.version,
                                         environment=step_result.testCase.session.environment,
                                         testStep=step_result.step).last()
        
        if not step_reference:
            return Response(status=status.HTTP_404_NOT_FOUND, data='no matching reference')
        
        # recompute when reference does not have detection_data or versions does not match
        if not step_reference.field_detection_data or step_reference.field_detection_version != form.cleaned_data['version']:
            field_detector_thread = FieldDetectorThread(step_reference)
            field_detector_thread.start()
            field_detector_thread.join()
        
        if step_reference.field_detection_data:
            
            if form.cleaned_data['output'] == 'image':
                # the detected image may or may not be here, if a 'detect' folder cleaning has been done
                return HttpResponse((detect_folder_path / os.path.basename(step_reference.image.name)).read_bytes(), content_type='image/png', status=200)
            else:
                return HttpResponse(step_reference.field_detection_data.read(), content_type='application/json', status=200)
            
        else:
            return Response(status=status.HTTP_404_NOT_FOUND, data="no field detection information")

    def post(self, request):
        """
        Method to send an image and get detection data (POST)
        
        to test: curl -F "image=@D:\Dev\yolo\yolov3\dataset_generated_small\out-7.jpg"   -F "task=field" http://127.0.0.1:8000/detect/
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





