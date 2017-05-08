import pickle

from rest_framework import views
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.PictureComparator import PictureComparator
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, TestStep, TestSession, Difference, \
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
            
            # check if a reference exists for this step in the same application / same version
            referenceSnapshots = Snapshot.objects.filter(step=step).filter(testCase__version=testCase.version).filter(isReference=True)
            if referenceSnapshots:
                m = Snapshot(step=step, image=image, testCase=testCase, isReference=False, session=session)
                m.save()
                
                # compute difference if a reference already exist
                pixelDiffs = PictureComparator().getChangedPixels(referenceSnapshots[0].image.path, m.image.path)
                binPixels = pickle.dumps(pixelDiffs, protocol=3)
                diff = Difference(reference=referenceSnapshots[0], compared=m, pixels=binPixels)
                diff.save()
            else:
                m = Snapshot(step=step, image=image, testCase=testCase, isReference=True, session=session)
                m.save()
                
            return Response(status=204)
        
        else:
            return Response(status=500)
