'''
Created on 4 mai 2017

@author: bhecquet
'''
from snapshotServer.serializers import SnapshotSerializer, TestStepSerializer, \
    TestSessionSerializer, ExcludeZoneSerializer, TestCaseInSessionSerializer,\
    StepResultSerializer, StepReferenceSerializer, FileSerializer, ExecutionLogsSerializer,\
    TestInfoSerializer
from rest_framework import viewsets, renderers
from snapshotServer.models import Snapshot, TestStep, TestSession, ExcludeZone, TestCaseInSession, StepResult,\
    StepReference, File, ExecutionLogs, TestInfo, Error
from commonsServer.views.viewsets import BaseViewSet
from rest_framework.decorators import action
from django.http.response import FileResponse, HttpResponse
from rest_framework.response import Response
import json
import zipfile
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import datetime
from django.utils import timezone

class TestSessionViewSet(BaseViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer

class TestCaseInSessionViewSet(viewsets.ModelViewSet):
    queryset = TestCaseInSession.objects.all()
    serializer_class = TestCaseInSessionSerializer

class TestInfoSessionViewSet(viewsets.ModelViewSet):
    queryset = TestInfo.objects.all()
    serializer_class = TestInfoSerializer

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
        elif instance.file.name.endswith('txt'):
            response = FileResponse(file_handle, content_type='text/plain')
        elif instance.file.name.endswith('avi'):
            response = FileResponse(file_handle, content_type='video/x-msvideo')
        elif instance.file.name.endswith('mp4'):
            response = FileResponse(file_handle, content_type='video/mp4')
        elif instance.file.name.endswith('zip'):
            response = FileResponse(file_handle, content_type='application/zip')
        else:
            response = FileResponse(file_handle, content_type='application/octet-stream')
        response['Content-Length'] = instance.file.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % instance.file.name

        return response
    
    def create(self, request, *args, **kwargs):
        """
        Creates a File object
        if the file is an HTML file, compress it
        """
        
        try:
            if request.FILES['file'].name.lower().endswith('.html'):
            
                with io.BytesIO() as zip_buffer:
        
                    with zipfile.ZipFile(zip_buffer, 'w') as zip:
                        zip.writestr(request.data['file'].name, request.FILES['file'].file.getvalue(), compress_type=zipfile.ZIP_DEFLATED)
        
                    in_memory_uploaded_file = InMemoryUploadedFile(zip_buffer, 'file', request.data['file'].name + '.zip', 'application/zip', zip_buffer.tell(), None)
                    file = File(stepResult=StepResult.objects.get(pk=int(request.data['stepResult'])), file=in_memory_uploaded_file)
                    file.save()
                    response = HttpResponse(json.dumps({'id': file.id}), status=201)
                    return response
            else:
                return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(status=500, data=json.dumps({'error': str(e)}))
            
    
class ExecutionLogsViewSet(viewsets.ModelViewSet):
    queryset = ExecutionLogs.objects.all()
    serializer_class = ExecutionLogsSerializer

class StepResultViewSet(viewsets.ModelViewSet):
    queryset = StepResult.objects.all()
    serializer_class = StepResultSerializer
    
    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.parse_stacktrace(serializer)
        
    def parse_stacktrace(self, serializer):
        """
        parse the stacktrace, looking for action in error
        """
        if not serializer.data['result']:
            try:
                step_result_details = json.loads(serializer.validated_data['stacktrace'])
                if step_result_details['name'] == 'Test end':
                    return
                
                failed_action, exception, exception_message = self.search_failed_action(step_result_details, step_result_details['action'])
                
                failed_action = failed_action if failed_action else step_result_details['name']
                exception = exception if exception else step_result_details['exception']
                exception_message = exception_message if exception_message else step_result_details['exceptionMessage']

                error = Error(stepResult = serializer.instance,
                              action = failed_action,
                              exception = exception,
                              errorMessage = exception_message,
                              )
                related_errors = self.search_related_errors(error)
                error.save()
                error.relatedErrors.set(related_errors)
                
            except Exception as e:
                pass
            
    def search_related_errors(self, error):
        """
        Search for similar errors in a time frame of 1 hour
        
        """
        return Error.objects.filter(
            action = error.action,
            exception = error.exception,
            errorMessage = error.errorMessage,
            stepResult__testCase__date__gte=timezone.now() - datetime.timedelta(seconds=3600)
            )

    def search_failed_action(self, data, path=''):
        """
        Look for an action that has the 'failed' flag set to true and return the name and the exception message, if it's present
        """

        if 'actions' in data:

            for action in data['actions']:
                
                if action.get('type') == 'step' and 'actions' in action:
                    failed_action, exception, exception_message = self.search_failed_action(action, path + '>' + action['action'])
                    if failed_action:
                        return failed_action, exception, exception_message

                if action.get('failed', False):
                    if action.get('element', ''):
                        return f"{path}>{action['action']} on {action['origin']}.{action['element']}", action.get('exception', None), action.get('exceptionMessage', None)
                    else:
                        return f"{path}>{action['action']} in {action['origin']}", action.get('exception', None), action.get('exceptionMessage', None)

        return None, None, None


    
class ExcludeZoneViewSet(BaseViewSet):
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
    
class StepReferenceViewSet(viewsets.ModelViewSet):
    queryset = StepReference.objects.all()
    serializer_class = StepReferenceSerializer
