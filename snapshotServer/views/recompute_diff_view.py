'''
Created on 26 juil. 2017

@author: worm
'''
from django.http.response import HttpResponse

from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import Snapshot
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultConsultation
from rest_framework.generics import get_object_or_404, CreateAPIView
from seleniumRobotServer.permissions import permissions

class RecomputeDiffPermission(ApplicationSpecificPermissionsResultConsultation):
    
    def get_object_application(self, snapshot):
        if snapshot:
            return snapshot.stepResult.testCase.session.version.application
        else:
            return ''
        
    def get_application(self, request, view):
        if view.kwargs.get('snapshot_id', ''): # POST
            return self.get_object_application(Snapshot.objects.get(pk=view.kwargs['snapshot_id']))
        else:
            return ''

class RecomputeDiffView(CreateAPIView):
    """
    API to compute diff from a REST request
    Called when changes has been applied to the list of exclude zones in step snapshot
    
    This API is called only from Web interface for now
    """
    
    queryset = Snapshot.objects.none()
    permission_classes = [RecomputeDiffPermission]
    
    def post(self, request, *args, **kwargs):

        step_snapshot = get_object_or_404(Snapshot, pk=kwargs['snapshot_id'])
        
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

        