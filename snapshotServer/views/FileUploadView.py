from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, TestStep, TestSession,\
    TestCaseInSession, StepResult


# Create your views here.
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
            stepResult = StepResult.objects.get(id=form.cleaned_data['stepResult'])
            image = form.cleaned_data['image']
            
            # check if a reference exists for this step in the same test case / same application / same version
            referenceSnapshots = Snapshot.objects.filter(stepResult__step=stepResult.step, stepResult__testCase__testCase__name=stepResult.testCase.testCase.name, refSnapshot=None)
            
            # check for a reference in previous versions
            if not referenceSnapshots:
                for appVersion in reversed(stepResult.testCase.session.version.previousVersions()):
                    referenceSnapshots = Snapshot.objects.filter(stepResult__step=stepResult.step, stepResult__testCase__testCase__name=stepResult.testCase.testCase.name, testCase__session__version=appVersion, refSnapshot=None)
                    if referenceSnapshots:
                        break
            
            if referenceSnapshots:
                stepSnapshot = Snapshot(stepResult=stepResult, image=image, refSnapshot=referenceSnapshots[0])
                stepSnapshot.save()
                
                # compute difference if a reference already exist
                DiffComputer.addJobs(referenceSnapshots[0], stepSnapshot)

            else:
                stepSnapshot = Snapshot(stepResult=stepResult, image=image, refSnapshot=None)
                stepSnapshot.save()
                
            return Response(status=204)
        
        else:
            return Response(status=500, data=str(form.errors))
        

