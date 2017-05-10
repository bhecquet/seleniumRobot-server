import pickle

from rest_framework import views
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.PictureComparator import PictureComparator
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, TestStep, TestSession, Difference, \
    TestCase
import threading
import time


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
            
            # check if a reference exists for this step in the same application / same version
            referenceSnapshots = Snapshot.objects.filter(step=step).filter(testCase__version=testCase.version).filter(isReference=True)
            if referenceSnapshots:
                stepSnapshot = Snapshot(step=step, image=image, testCase=testCase, isReference=False, session=session)
                stepSnapshot.save()
                
                # compute difference if a reference already exist
                DiffComputer(referenceSnapshots[0], stepSnapshot).start()
#                 pixelDiffs = PictureComparator().getChangedPixels(.image.path, stepSnapshot.image.path)
#                 binPixels = pickle.dumps(pixelDiffs, protocol=3)
#                 diff = Difference(reference=referenceSnapshots[0], compared=stepSnapshot, pixels=binPixels)
#                 diff.save()
            else:
                stepSnapshot = Snapshot(step=step, image=image, testCase=testCase, isReference=True, session=session)
                stepSnapshot.save()
                
            return Response(status=204)
        
        else:
            return Response(status=500)
        
class DiffComputer(threading.Thread):
    """
    Class for processing differences asynchronously
    """
    
    def __init__(self, refSnapshot, stepSnapshot):
        self.refSnapshot = refSnapshot
        self.stepSnapshot = stepSnapshot
        super(DiffComputer, self).__init__()
    
    def run(self):
        print('starting')
        pixelDiffs = PictureComparator().getChangedPixels(self.refSnapshot.image.path, self.stepSnapshot.image.path)
        binPixels = pickle.dumps(pixelDiffs, protocol=3)
        diff = Difference(reference=self.refSnapshot, compared=self.stepSnapshot, pixels=binPixels)
        diff.save()
        print('finished')
