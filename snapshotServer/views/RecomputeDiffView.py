'''
Created on 26 juil. 2017

@author: worm
'''
from django.http.response import HttpResponse
from django.views.generic.base import View

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional


class RecomputeDiffView(LoginRequiredMixinConditional, View):
    """
    API to compute diff from a REST request
    Called when changes has been applied to the list of exclude zones in step snapshot
    """
    
    queryset = Snapshot.objects.none()
    
    def post(self, request, *args, **kwargs):
        try:
            step_snapshot = Snapshot.objects.get(pk=args[0])
            
            # compute has sense when a reference exists
            if step_snapshot.refSnapshot:
                DiffComputer.computeNow(step_snapshot.refSnapshot, step_snapshot)
                
                # start computing differences for other snapshots sharing the same reference
                for snap in step_snapshot.snapshotWithSameRef():
                    DiffComputer.addJobs(step_snapshot.refSnapshot, snap)
                
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=304)
                
        except Exception as e:
            return HttpResponse(status=404)
        