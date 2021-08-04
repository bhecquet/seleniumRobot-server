import json

from django.http.response import HttpResponse, StreamingHttpResponse
from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from snapshotServer.forms import ImageForStepReferenceUploadForm
from snapshotServer.models import StepResult, StepReference
import mimetypes


class StepReferenceView(views.APIView):
    """
    View of the API to upload a file with step reference (mainly, a snapshot)
    Different from FileUploadView which aims at comparing snapshot with a reference
    """
    
    parser_classes = (MultiPartParser,)
    queryset = StepResult.objects.all()

    # test with CURL
    # curl -u admin:adminServer -F "step=1" -F "testCase=1" -F "sessionId=1234" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/upload/toto
    def post(self, request, format=None):
        
        form = ImageForStepReferenceUploadForm(request.POST, request.FILES)
        
        
        if form.is_valid():
            step_result = StepResult.objects.get(id=form.cleaned_data['stepResult'])
            image = form.cleaned_data['image']
            
            # only store reference when result is OK
            if step_result.result:
                step_reference = StepReference.objects.filter(stepResult__testCase__testCase__name=step_result.testCase.testCase.name, 
                                             stepResult__testCase__session__version=step_result.testCase.session.version,
                                             stepResult__testCase__session__environment=step_result.testCase.session.environment,
                                             stepResult__step=step_result.step).order_by('pk').last()
                                             
                if not step_reference:
                    StepReference(stepResult=step_result, image=image).save()
                else:
                    step_reference.stepResult = step_result
                    step_reference.image = image
                    step_reference.save()
            
                
            return HttpResponse(json.dumps({'result': 'OK'}), content_type='application/json', status=201)
        
        else:
            return Response(status=500, data=str(form.errors))
        

    def get(self, request, step_result_id):
        """
        Get the reference image corresponding to this StepResult. We get the application / version / test case / environment from this StepResult 
        """
        
        step_result = StepResult.objects.get(id=step_result_id)
        
        # get the step reference corresponding to the same testCase/testStep
        step_reference = StepReference.objects.filter(stepResult__testCase__testCase=step_result.testCase.testCase, 
                                             stepResult__testCase__session__version=step_result.testCase.session.version,
                                             stepResult__testCase__session__environment=step_result.testCase.session.environment,
                                             stepResult__step=step_result.step)
    
        if not step_reference:
            return HttpResponse(json.dumps({'error': 'no matching reference'}), content_type='application/json', status=404)
        else:
            step_reference = step_reference[0]
            content_type_file = mimetypes.guess_type(step_reference.image.path)[0]
            # response = StreamingHttpResponse(open(step_reference.image.path, 'rb'), content_type=content_type_file)
            # response['Content-Disposition'] = "attachment; filename=%s" % str(step_reference.image)
            # response['Content-Length'] = step_reference.image.size
            response = HttpResponse(open(step_reference.image.path, 'rb'), content_type=content_type_file, status=200)
            return response