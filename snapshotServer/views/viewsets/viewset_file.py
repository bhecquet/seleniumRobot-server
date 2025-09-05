import json
import zipfile
import io
from http.client import HTTPResponse

from rest_framework import renderers, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from django.http.response import FileResponse
from django.core.files.uploadedfile import InMemoryUploadedFile

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import StepResult, File
from snapshotServer.viewsets import ResultRecordingViewSet



class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'stepResult', 'file', 'name')

class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = ''
    format = ''
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

class FilePermission(ApplicationSpecificPermissionsResultRecording):
    """
    Redefine permission class so that it's possible to get application from data
    """

    def get_object_application(self, file):
        if file:
            return file.stepResult.testCase.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        if request.POST.get('stepResult', ''): # POST
            return StepResult.objects.get(pk=request.data['stepResult']).testCase.session.version.application
        elif view.kwargs.get('pk', ''): # GET, needed so that we can refuse access if object is unknown
            return self.get_object_application(File.objects.get(pk=view.kwargs['pk']))
        else:
            return ''

class FileViewSet(ResultRecordingViewSet): # post
    """
    View allowing to upload any file that has been produced by test
    - logs
    - video
    - pictures
    - html
    - ...
    """

    http_method_names = ['post', 'get']
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [FilePermission]

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
        filename = instance.name if instance.name else instance.file.name
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename

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
                    response = HTTPResponse(json.dumps({'id': file.id}), status=201)
                    return response
            else:
                return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(status=500, data=json.dumps({'error': str(e)}))
