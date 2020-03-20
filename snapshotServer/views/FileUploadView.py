from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, TestStep, TestSession,\
    TestCaseInSession, StepResult
import json
from django.http.response import HttpResponse



class FileUploadView(views.APIView):
    """
    View of the API to upload a file with snapshot informations
    It creates the snapshot and detects if a reference already exists for this snapshot
    """
    
    parser_classes = (MultiPartParser,)
    queryset = Snapshot.objects.all()

    # test with CURL
    # curl -u admin:adminServer -F "step=1" -F "testCase=1" -F "sessionId=1234" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/upload/toto
    def post(self, request, filename, format=None):
        
        form = ImageUploadForm(request.POST, request.FILES)
        
        
        if form.is_valid():
            step_result = StepResult.objects.get(id=form.cleaned_data['stepResult'])
            image = form.cleaned_data['image']
            name = form.cleaned_data['name']
            compare_option = form.cleaned_data.get('compare', 'true')
            
            # check if a reference exists for this step in the same test case / same application / same version / same name
            reference_snapshots = Snapshot.objects.filter(stepResult__step=step_result.step, 
                                                          stepResult__testCase__testCase__name=step_result.testCase.testCase.name, 
                                                          refSnapshot=None,
                                                          name=name)
            
            # check for a reference in previous versions
            if not reference_snapshots:
                for app_version in reversed(step_result.testCase.session.version.previousVersions()):
                    reference_snapshots = Snapshot.objects.filter(stepResult__step=step_result.step, 
                                                                  stepResult__testCase__testCase__name=step_result.testCase.testCase.name, 
                                                                  stepResult__testCase__session__version=app_version, 
                                                                  refSnapshot=None,
                                                                  name=name)
                    if reference_snapshots:
                        break
            
            if reference_snapshots:
                step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=reference_snapshots[0], name=name, compareOption=compare_option)
                step_snapshot.save()
                
                # compute difference if a reference already exist
                DiffComputer.addJobs(reference_snapshots[0], step_snapshot)

            else:
                step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=None, name=name, compareOption=compare_option)
                step_snapshot.save()
                
            return HttpResponse(json.dumps({'id': step_snapshot.id}), content_type='application/json', status=201)
        
        else:
            return Response(status=500, data=str(form.errors))
        

