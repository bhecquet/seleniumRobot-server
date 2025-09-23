from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import ExcludeZone, Snapshot
from snapshotServer.viewsets import ResultRecordingViewSet


class ExcludeZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExcludeZone
        fields = ('id', 'x', 'y', 'width', 'height', 'snapshot')

class ExcludeZonePermission(ApplicationSpecificPermissionsResultRecording):

    def get_object_application(self, exclude_zone):
        if exclude_zone:
            return exclude_zone.snapshot.stepResult.testCase.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        if request.POST.get('snapshot', ''): # POST
            return Snapshot.objects.get(pk=request.data['snapshot']).stepResult.testCase.session.version.application
        elif view.kwargs.get('pk', ''): # PATCH / DELETE, needed so that we can refuse access if object is unknown
            return self.get_object_application(ExcludeZone.objects.get(pk=view.kwargs['pk']))
        else:
            return ''

class ExcludeZoneViewSet(ResultRecordingViewSet): # post
    http_method_names = ['post', 'patch', 'delete']
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
    permission_classes = [ExcludeZonePermission]
    recreate_existing_instance = False