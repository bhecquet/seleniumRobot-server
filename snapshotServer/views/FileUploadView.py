import pickle
import threading
import time

from rest_framework import views
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.PictureComparator import PictureComparator, \
    DiffComputer
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, TestStep, TestSession, \
    TestCase


# Create your views here.
class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)
    queryset = Snapshot.objects.all()

    # test with CURL
    # curl -u admin:adminServer -F "step=1" -F "testCase=1" -F "sessionId=1234" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/upload/toto
    def post(self, request, filename, format=None):
        
        form = ImageUploadForm(request.POST, request.FILES)
        
        
        
        if form.is_valid():
            step = TestStep.objects.get(id=form.cleaned_data['step'])
            session = TestSession.objects.get(sessionId=form.cleaned_data['sessionId'])
            testCase = TestCase.objects.get(id=form.cleaned_data['testCase'])
            image = form.cleaned_data['image']
            
            # check if a reference exists for this step in the same test case / same application / same version
            referenceSnapshots = Snapshot.objects.filter(step=step, testCase=testCase, refSnapshot=None)
            
            # check for a reference in previous versions
            if not referenceSnapshots:
                for appVersion in reversed(testCase.version.previousVersions()):
                    referenceSnapshots = Snapshot.objects.filter(step=step, testCase__name=testCase.name, testCase__version=appVersion, refSnapshot=None)
                    if referenceSnapshots:
                        break
            
            if referenceSnapshots:
                stepSnapshot = Snapshot(step=step, image=image, testCase=testCase, refSnapshot=referenceSnapshots[0], session=session)
                stepSnapshot.save()
                
                # compute difference if a reference already exist
                DiffComputer(referenceSnapshots[0], stepSnapshot).start()

            else:
                stepSnapshot = Snapshot(step=step, image=image, testCase=testCase, refSnapshot=None, session=session)
                stepSnapshot.save()
                
            return Response(status=204)
        
        else:
            return Response(status=500)
        

