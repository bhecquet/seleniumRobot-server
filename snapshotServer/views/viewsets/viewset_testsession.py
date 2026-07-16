from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ContextSpecificPermissionsResultRecording
from snapshotServer.models import Version, TestSession, TestEnvironment
from snapshotServer.viewsets import ResultRecordingViewSet


class TestSessionSerializer(serializers.ModelSerializer):

    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())

    class Meta:
        model = TestSession
        fields = ('id', 'sessionId', 'date', 'browser', 'environment', 'version', 'compareSnapshot', 'compareSnapshotBehaviour', 'name', 'ttl', 'startedBy')


class TestSessionPermission(ContextSpecificPermissionsResultRecording):

    def get_application(self, request, view):
        if request.POST.get('version', ''): # POST
            return Version.objects.get(pk=request.data['version']).application
        else:
            return ''

    def get_environment(self, request, view):
        if request.POST.get('environment', ''): # POST
            return TestEnvironment.objects.get(name=request.data['environment'])
        else:
            return ''

class TestSessionViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post']
    queryset = TestSession.objects.none()
    serializer_class = TestSessionSerializer
    recreate_existing_instance = False
    permission_classes = [TestSessionPermission]
