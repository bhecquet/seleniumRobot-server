'''
Created on 26 juil. 2017

@author: worm
'''
from django.http.response import HttpResponse

from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import Snapshot
from commonsServer.views.viewsets import ApplicationSpecificViewSet
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultConsultation
from rest_framework.generics import get_object_or_404
from seleniumRobotServer.permissions import permissions


class RecomputeDiffView(ApplicationSpecificViewSet):
    """
    API to compute diff from a REST request
    Called when changes has been applied to the list of exclude zones in step snapshot
    
    This API is called only from Web interface for now
    """
    
    queryset = Snapshot.objects.none()
    permission_classes = [ApplicationSpecificPermissionsResultConsultation]
    prefix = permissions.APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX
    
    def get_object_application(self, step_snapshot):
        if step_snapshot:
            return step_snapshot.stepResult.testCase.session.version.application
        else:
            return ''
    
    def post(self, request, *args, **kwargs):

        step_snapshot = get_object_or_404(Snapshot, pk=args[0])
        self.check_object_permissions(request, step_snapshot)
        
        # compute has sense when a reference exists
        if step_snapshot.refSnapshot:
            
            diff_computer = DiffComputer.get_instance()
            diff_computer.compute_now(step_snapshot.refSnapshot, step_snapshot)
            
            # start computing differences for other snapshots sharing the same reference
            for snap in step_snapshot.snapshotWithSameRef():
                diff_computer.add_jobs(step_snapshot.refSnapshot, snap)
            
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=304)

        