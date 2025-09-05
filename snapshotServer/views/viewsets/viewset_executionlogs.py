from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import ExecutionLogs, TestCaseInSession
from snapshotServer.viewsets import ResultRecordingViewSet


class ExecutionLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionLogs
        fields = ('id', 'testCase', 'file')

class ExecutionLogsPermission(ApplicationSpecificPermissionsResultRecording):

    def get_application(self, request, view):
        if request.POST.get('testCase', ''): # POST
            return TestCaseInSession.objects.get(pk=request.data['testCase']).session.version.application
        else:
            return ''

class ExecutionLogsViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post']
    queryset = ExecutionLogs.objects.all()
    serializer_class = ExecutionLogsSerializer
    permission_classes = [ExecutionLogsPermission]