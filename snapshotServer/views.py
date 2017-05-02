import pickle

from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from rest_framework import viewsets, views
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.PictureComparator import PictureComparator
from snapshotServer.forms import ImageUploadForm
from snapshotServer.models import Snapshot, Application, TestEnvironment, \
    TestCase, TestStep, Difference, Version, TestSession
from snapshotServer.serializers import UserSerializer, GroupSerializer, \
    SnapshotSerializer, ApplicationSerializer, TestEnvironmentSerializer, \
    TestCaseSerializer, TestStepSerializer, VersionSerializer, \
    TestSessionSerializer


# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    
class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    
class TestEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = TestEnvironment.objects.all()
    serializer_class = TestEnvironmentSerializer
    
class TestSessionViewSet(viewsets.ModelViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer
    
class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    
class TestStepViewSet(viewsets.ModelViewSet):
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    
class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
    
class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)
    queryset = Snapshot.objects.all()

    # test with CURL
    # curl -u admin:adminServer -F "step=1" -F "browser=firefox" -F "sessionId=1234" -F "image=@/home/worm/Ibis Mulhouse.png"   http://127.0.0.1:8000/upload/toto
    def post(self, request, filename, format=None):
        
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            step = TestStep.objects.get(id=form.cleaned_data['step'])
            session = TestSession.objects.get(sessionId=form.cleaned_data['sessionId'])
            
            # check if a reference exists for this step
            referenceSnapshots = Snapshot.objects.filter(step=step).filter(isReference=True)
            if referenceSnapshots:
                m = Snapshot(step=step, image=form.cleaned_data['image'], browser=form.cleaned_data['browser'], isReference=False, session=session)
                m.save()
                
                # compute difference if a reference already exist
                pixelDiffs = PictureComparator().getChangedPixels(referenceSnapshots[0].image.path, m.image.path)
                binPixels = pickle.dumps(pixelDiffs, protocol=3)
                diff = Difference(reference=referenceSnapshots[0], compared=m, pixels=binPixels)
                diff.save()
            else:
                m = Snapshot(step=step, image=form.cleaned_data['image'], browser=form.cleaned_data['browser'], isReference=True, session=session)
                m.save()
        
            
        
            return Response(status=204)
        
        else:
            return Response(status=500)
