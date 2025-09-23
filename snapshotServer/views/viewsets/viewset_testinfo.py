from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import TestCaseInSession, TestInfo
from snapshotServer.viewsets import ResultRecordingViewSet



class TestInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestInfo
        fields = ('id', 'testCase', 'name', 'info')


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