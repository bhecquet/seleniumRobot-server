'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView

from snapshotServer.models import ExcludeZone


class ExclusionZoneListView(ListView):
    template_name = "snapshotServer/excludeList.html"
    
    def get_queryset(self):
        return ExcludeZone.objects.filter(snapshot=self.kwargs['snapshotId'])