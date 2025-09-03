'''
Created on 4 mai 2017

@author: bhecquet
'''
import datetime
import io
import json
import zipfile

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.aggregates import Count
from django.http.response import FileResponse, HttpResponse
from django.utils import timezone
from rest_framework import viewsets, renderers
from rest_framework.decorators import action
from rest_framework.generics import UpdateAPIView, CreateAPIView, \
    RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated

from commonsServer.views.viewsets import BaseViewSet
from seleniumRobotServer.permissions import permissions
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording, \
    ApplicationPermissionChecker
from snapshotServer.models import TestStep, TestSession, ExcludeZone, TestCaseInSession, StepResult, \
    File, ExecutionLogs, TestInfo, Error, Version, Application
from snapshotServer.serializers import TestStepSerializer, \
    TestSessionSerializer, ExcludeZoneSerializer, TestCaseInSessionSerializer, \
    StepResultSerializer, FileSerializer, ExecutionLogsSerializer, \
    TestInfoSerializer


class ResultRecordingViewSet(ViewSet,
                             CreateAPIView, # POST
                             RetrieveAPIView, # GET
                             UpdateAPIView # PATCH
                             ):
    permission_classes = [ApplicationSpecificPermissionsResultRecording]
    recreate_existing_instance = True 
    
    def perform_create(self, serializer):
        """
        Check if we need to recreate or not the object
        """
        if self.recreate_existing_instance:
            super().perform_create(serializer)
            return
        
        # Do not create an object if it already exists
        objects = self.serializer_class.Meta.model.objects.all()
        for key, value in serializer.validated_data.items():
            if type(value) == list:
                objects = objects.annotate(Count(key)).filter(**{key + '__count': len(value)})
                if len(value) > 0:
                    for v in value:
                        objects = objects.filter(**{key: v})
            else:
                objects = objects.filter(**{key: value})
    
        if not objects:
            super().perform_create(serializer)
        else:
            serializer.data.serializer._data.update({'id': objects[0].id})

    @classmethod
    def get_extra_actions(cls):
        return []


class TestSessionPermission(ApplicationSpecificPermissionsResultRecording):
    """
    Redefine permission class so that it's possible to get application from data
    """

    def get_application(self, request, view):
        if request.POST.get('version', ''): # POST
            return Version.objects.get(pk=request.data['version']).application
        else:
            return ''

class TestSessionViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post']
    queryset = TestSession.objects.none()
    serializer_class = TestSessionSerializer
    recreate_existing_instance = False 
    permission_classes = [TestSessionPermission]

class TestCaseInSessionPermission(ApplicationSpecificPermissionsResultRecording):
    """
    Redefine permission class so that it's possible to get application from data
    """

    def get_object_application(self, test_case_in_session):
        if test_case_in_session:
            return test_case_in_session.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        if request.POST.get('session', ''): # POST
            return TestSession.objects.get(pk=request.data['session']).version.application
        elif view.kwargs.get('pk', ''): # PATCH / GET, needed so that we can refuse access if object is unknown
            return self.get_object_application(TestCaseInSession.objects.get(pk=view.kwargs['pk']))
        else:
            return ''

class TestCaseInSessionViewSet(ResultRecordingViewSet): # post / get / patch
    http_method_names = ['post', 'get', 'patch']
    queryset = TestCaseInSession.objects.all()
    serializer_class = TestCaseInSessionSerializer
    permission_classes = [TestCaseInSessionPermission]

class TestInfoSessionPermission(ApplicationSpecificPermissionsResultRecording):

    def get_application(self, request, view):
        if request.POST.get('testCase', ''): # POST
            return TestCaseInSession.objects.get(pk=request.data['testCase']).session.version.application
        else:
            return ''

class TestInfoSessionViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post']
    queryset = TestInfo.objects.all()
    serializer_class = TestInfoSerializer
    permission_classes = [TestInfoSessionPermission]

class TestStepPermission(ApplicationSpecificPermissionsResultRecording):
    """
    Allow any user that has right on at least an application, to create step
    """

    def get_application(self, request, view):
        allowed_applications = ApplicationPermissionChecker.get_allowed_applications(request, self.prefix)
        if allowed_applications:
            return Application.objects.get(name=allowed_applications[0])
        else:
            return ''

class TestStepViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post']
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    recreate_existing_instance = False
    permission_classes = [TestStepPermission]

class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = ''
    format = ''
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
    
class FileViewSet(viewsets.ModelViewSet): # post
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
            
    
class ExecutionLogsViewSet(viewsets.ModelViewSet): # post
    queryset = ExecutionLogs.objects.all()
    serializer_class = ExecutionLogsSerializer

class StepResultViewSet(viewsets.ModelViewSet): # post / patch
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


    
class ExcludeZoneViewSet(BaseViewSet): # post
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
