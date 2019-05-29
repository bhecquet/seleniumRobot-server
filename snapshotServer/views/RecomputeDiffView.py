'''
Created on 26 juil. 2017

@author: worm
'''
from django.http.response import HttpResponse
from django.views.generic.base import View

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot


class RecomputeDiffView(View):
    """
    API to compute diff from a REST request
    """
    
    queryset = Snapshot.objects.none()
    
    def post(self, request, *args, **kwargs):
        try:
            stepSnapshot = Snapshot.objects.get(pk=args[0])
            
            # compute has sense when a reference exists
            if stepSnapshot.refSnapshot:
                DiffComputer.computeNow(stepSnapshot.refSnapshot, stepSnapshot)
                
                # start computing differences for other snapshots sharing the same reference
                for snap in stepSnapshot.snapshotWithSameRef():
                    DiffComputer.addJobs(stepSnapshot.refSnapshot, snap)
                
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=304)
                
        except:
            return HttpResponse(status=404)
        