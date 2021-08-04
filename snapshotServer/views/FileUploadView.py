from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.forms import ImageForComparisonUploadForm
from snapshotServer.models import Snapshot, StepResult
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
        
        form = ImageForComparisonUploadForm(request.POST, request.FILES)
        
        
        if form.is_valid():
            step_result = StepResult.objects.get(id=form.cleaned_data['stepResult'])
            image = form.cleaned_data['image']
            name = form.cleaned_data['name']
            diff_tolerance = form.cleaned_data.get('diffTolerance', 0.0)
            compare_option = form.cleaned_data.get('compare', 'true')
            
            # check if a reference exists for this step in the same test case / same application / same version / same environment / same browser / same name
            most_recent_reference_snapshot = Snapshot.objects.filter(stepResult__step=step_result.step,                                                    # same step in the test case
                                                          stepResult__testCase__testCase__name=step_result.testCase.testCase.name,              # same test case
                                                          stepResult__testCase__session__version=step_result.testCase.session.version,          # same version
                                                          stepResult__testCase__session__environment=step_result.testCase.session.environment,  # same environment
                                                          stepResult__testCase__session__browser=step_result.testCase.session.browser,          # same browser
                                                          refSnapshot=None,                                                                     # a reference image
                                                          name=name).order_by('pk').last()                                                                          # same snapshot name
            
            # check for a reference in previous versions
            if not most_recent_reference_snapshot:
                for app_version in reversed(step_result.testCase.session.version.previousVersions()):
                    most_recent_reference_snapshot = Snapshot.objects.filter(stepResult__step=step_result.step, 
                                                                  stepResult__testCase__testCase__name=step_result.testCase.testCase.name, 
                                                                  stepResult__testCase__session__version=app_version, 
                                                                  stepResult__testCase__session__environment=step_result.testCase.session.environment, 
                                                                  stepResult__testCase__session__browser=step_result.testCase.session.browser, 
                                                                  refSnapshot=None,
                                                                  name=name).order_by('pk').last()     
                    if most_recent_reference_snapshot:
                        break
            
            if most_recent_reference_snapshot:
                step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=most_recent_reference_snapshot, name=name, compareOption=compare_option, diffTolerance=diff_tolerance)
                step_snapshot.save()
                
                # compute difference if a reference already exist
                DiffComputer.get_instance().add_jobs(most_recent_reference_snapshot, step_snapshot)

            else:
                # snapshot is marked as computed as this is a reference snapshot
                step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=None, name=name, compareOption=compare_option, computed=True, diffTolerance=diff_tolerance)
                step_snapshot.save()
                
            return HttpResponse(json.dumps({'id': step_snapshot.id}), content_type='application/json', status=201)
        
        else:
            return Response(status=500, data=str(form.errors))
        

