from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording, \
    ApplicationPermissionChecker
from snapshotServer.models import TestStep, Application
from snapshotServer.viewsets import ResultRecordingViewSet


class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ('id', 'name')

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
