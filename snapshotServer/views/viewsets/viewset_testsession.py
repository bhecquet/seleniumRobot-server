from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import Version, TestSession, TestEnvironment
from snapshotServer.viewsets import ResultRecordingViewSet


class TestSessionSerializer(serializers.ModelSerializer):

    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())

    class Meta:
        model = TestSession
        fields = ('id', 'sessionId', 'date', 'browser', 'environment', 'version', 'compareSnapshot', 'compareSnapshotBehaviour', 'name', 'ttl', 'startedBy')


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
