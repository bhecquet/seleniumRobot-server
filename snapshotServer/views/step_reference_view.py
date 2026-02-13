import json
import mimetypes
import threading

from datetime import datetime

from django.http.response import HttpResponse
from django.utils import timezone

from rest_framework.parsers import MultiPartParser

from snapshotServer.models import StepResult, StepReference
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from rest_framework.generics import get_object_or_404, RetrieveAPIView, CreateAPIView
from rest_framework import serializers

class NoStepReferenceToCreate(Exception):
    pass

class StepReferenceSerializer(serializers.ModelSerializer):
    
    image = serializers.FileField(required=True) # use a FileField instead of an ImageField, so that unittest don't break when we submit a non-image file
    stepResult = serializers.PrimaryKeyRelatedField(required=True, queryset=StepResult.objects.all())
    
    class Meta:
        model = StepReference
        fields = ('stepResult', 'image')
        
     
    def create(self, validated_data):
        """
        Override the create method, so that we can update validated_data
        """
        step_result = validated_data['stepResult']
        image = validated_data['image']
        
        # only store reference when result is OK
        if step_result.result:
            # search an existing reference for the same testCase / testStep / version / environment
            step_reference = StepReference.objects.filter(testCase=step_result.testCase.testCase, 
                                         version=step_result.testCase.session.version,
                                         environment=step_result.testCase.session.environment,
                                         testStep=step_result.step).order_by('pk').last()
                                         
            if not step_reference:
                step_reference = StepReference(testCase=step_result.testCase.testCase, 
                             version=step_result.testCase.session.version,
                             environment=step_result.testCase.session.environment,
                             testStep=step_result.step,
                             image=image)
                step_reference.save()
                
            # do not update reference if it has been upated in the last 48h
            # this prevent from computing on every test run
            elif (timezone.now() - step_reference.date).seconds < StepReferenceView.OVERWRITE_REFERENCE_AFTER_SECONDS:
                return step_reference
            else:
                
                if image is not None:
                    step_reference.image.delete(save=False)
                step_reference.image = image
                step_reference.save()
            
            return step_reference
        
        else:
            raise NoStepReferenceToCreate()
        
class StepReferencePermission(ApplicationSpecificPermissionsResultRecording):
    
    def get_object_application(self, step_result):
        if step_result:
            return step_result.testCase.session.version.application
        else:
            return ''
        
    def get_application(self, request, view):
        if request.POST.get('stepResult', ''): # POST
            return self.get_object_application(StepResult.objects.get(pk=request.data['stepResult']))
        elif view.kwargs.get('step_result_id', ''): # GET
            return self.get_object_application(StepResult.objects.get(pk=view.kwargs['step_result_id']))
        else:
            return ''

class StepReferenceView(CreateAPIView, RetrieveAPIView):
    """
    View of the API to upload a file with step reference (mainly, a snapshot)
    SeleniumRobot-core will get this reference when a step fails
    This will try to detect fields / texts / errors on the reference
    
    StepReferenceView is only used by core for result pushing / getting results
    
    Different from FileUploadView which aims at comparing snapshot with a reference for visual non-regression
    """
    
    parser_classes = (MultiPartParser,)
    queryset = StepReference.objects.none()
    last_clean = datetime.today()
    last_clean_lock = threading.Lock()
    permission_classes = [StepReferencePermission]
    serializer_class = StepReferenceSerializer

    OVERWRITE_REFERENCE_AFTER_SECONDS = 60 * 60 * 12    # in case a reference already exist, overwrite it only after X seconds (12 hours by default)

    def post(self, request, *args, **kwargs):
        """
        test with CURL
        curl -u admin:adminServer -F "stepResult=1" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/stepReference/
        """

        try:
            return self.create(request, *args, **kwargs)
        except NoStepReferenceToCreate as e:
            return HttpResponse(json.dumps({'result': 'OK'}), content_type='application/json', status=200)

    def get(self, request, step_result_id):
        """
        Get the reference image corresponding to this StepResult. We get the application / version / test case / environment from this StepResult 
        """
        
        step_result = get_object_or_404(StepResult, id=step_result_id)
        
        # get the step reference corresponding to the same testCase/testStep
        step_reference = StepReference.objects.filter(testCase=step_result.testCase.testCase, 
                                             version=step_result.testCase.session.version,
                                             environment=step_result.testCase.session.environment,
                                             testStep=step_result.step)
    
        if not step_reference:
            return HttpResponse(json.dumps({'error': 'no matching reference'}), content_type='application/json', status=404)
        else:
            step_reference = step_reference[0]
            content_type_file = mimetypes.guess_type(step_reference.image.path)[0]
            
            # Streaming of file has been disable because Unirest (of seleniumRobot) cannot handle it
            # response = StreamingHttpResponse(open(step_reference.image.path, 'rb'), content_type=content_type_file)
            # response['Content-Disposition'] = "attachment; filename=%s" % str(step_reference.image)
            # response['Content-Length'] = step_reference.image.size
            response = HttpResponse(open(step_reference.image.path, 'rb'), content_type=content_type_file, status=200)
            return response
        