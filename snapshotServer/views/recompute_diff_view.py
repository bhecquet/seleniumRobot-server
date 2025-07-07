'''
Created on 26 juil. 2017

@author: worm
'''
from django.http.response import HttpResponse

from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import Snapshot
from commonsServer.views.viewsets import ApplicationSpecificViewSet
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultConsultation


class RecomputeDiffView(ApplicationSpecificViewSet):
    """
    API to compute diff from a REST request
    Called when changes has been applied to the list of exclude zones in step snapshot
    
    This API is called only from Web interface for now
    """
    
    queryset = Snapshot.objects.none()
    permission_classes = [ApplicationSpecificPermissionsResultConsultation]
    
    def post(self, request, *args, **kwargs):
        try:
            step_snapshot = Snapshot.objects.get(pk=args[0])
            
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
                
        except Exception as e:
            return HttpResponse(status=404)
        