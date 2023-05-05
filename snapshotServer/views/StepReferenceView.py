import json

from django.http.response import HttpResponse, StreamingHttpResponse
from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from multiprocessing import Process

from snapshotServer.forms import ImageForStepReferenceUploadForm
from snapshotServer.models import StepResult, StepReference
import mimetypes
import os
from snapshotServer.controllers.FieldDetector import FieldDetectorThread

# TESTs
# - calcul de field en même temps que la référence
# - si le calcul échoue, cela ne doit pas bloquer

class StepReferenceView(views.APIView):
    """
    View of the API to upload a file with step reference (mainly, a snapshot)
    Different from FileUploadView which aims at comparing snapshot with a reference
    """
    
    parser_classes = (MultiPartParser,)
    queryset = StepResult.objects.all()

    def post(self, request, format=None):
        """
        test with CURL
        curl -u admin:adminServer -F "stepResult=1" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/stepReference/
        """
        
        form = ImageForStepReferenceUploadForm(request.POST, request.FILES)
        
        
        if form.is_valid():
            step_result = StepResult.objects.get(id=form.cleaned_data['stepResult'])
            image = form.cleaned_data['image']
            
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
                else:
                    
                    if image is not None:
                        old_path = step_reference.image.path
                    else:
                        old_path = None
                    step_reference.image = image
                    step_reference.save()
                    
                    try:
                        os.remove(old_path)
                    except (FileNotFoundError, TypeError, PermissionError) as e:
                        pass
                
                # detect fields on reference image
                # then, if an error occurs in test, it won't be necessary to compute both reference image and step image
                FieldDetectorThread(step_reference).start()        
                
                
            return HttpResponse(json.dumps({'result': 'OK'}), content_type='application/json', status=201)
        
        else:
            return Response(status=500, data=str(form.errors))
        

    def get(self, request, step_result_id):
        """
        Get the reference image corresponding to this StepResult. We get the application / version / test case / environment from this StepResult 
        """
        
        step_result = StepResult.objects.get(id=step_result_id)
        
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
        