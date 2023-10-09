'''
Created on 4 mai 2017

@author: bhecquet
'''
from snapshotServer.serializers import SnapshotSerializer, TestStepSerializer, \
    TestSessionSerializer, ExcludeZoneSerializer, TestCaseInSessionSerializer,\
    StepResultSerializer, StepReferenceSerializer, FileSerializer, ExecutionLogsSerializer
from rest_framework import viewsets, renderers
from snapshotServer.models import Snapshot, TestStep, TestSession, ExcludeZone, TestCaseInSession, StepResult,\
    StepReference, File, ExecutionLogs
from commonsServer.views.viewsets import BaseViewSet
from commonsServer.views.serializers import ApplicationSerializer
from rest_framework.decorators import action
from django.http.response import FileResponse

class TestSessionViewSet(BaseViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer

class TestCaseInSessionViewSet(viewsets.ModelViewSet):
    queryset = TestCaseInSession.objects.all()
    serializer_class = TestCaseInSessionSerializer

class TestStepViewSet(BaseViewSet):
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    
class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
    
class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = ''
    format = ''
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
    
class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    
    @action(methods=['get'], detail=True, renderer_classes=(PassthroughRenderer,))
    def download(self, *args, **kwargs):
        instance = self.get_object()

        # get an open file handle 
        file_handle = instance.file.open()

        # send file
        if instance.file.name.endswith('png'):
            response = FileResponse(file_handle, content_type='image/png')
        elif instance.file.name.endswith('html'):
            response = FileResponse(file_handle, content_type='text/html')
        elif instance.file.name.endswith('avi'):
            response = FileResponse(file_handle, content_type='video/x-msvideo')
        else:
            response = FileResponse(file_handle, content_type='application/octet-stream')
        response['Content-Length'] = instance.file.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % instance.file.name

        return response
    
class ExecutionLogsViewSet(viewsets.ModelViewSet):
    queryset = ExecutionLogs.objects.all()
    serializer_class = ExecutionLogsSerializer

class StepResultViewSet(viewsets.ModelViewSet):
    queryset = StepResult.objects.all()
    serializer_class = StepResultSerializer
    
class ExcludeZoneViewSet(BaseViewSet):
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
    
class StepReferenceViewSet(viewsets.ModelViewSet):
    queryset = StepReference.objects.all()
    serializer_class = StepReferenceSerializer
