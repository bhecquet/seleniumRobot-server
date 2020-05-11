'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView
from django.db.models import Q

from snapshotServer.models import ExcludeZone
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional



class ExclusionZoneListView(LoginRequiredMixinConditional, ListView):
    """
    View displaying list of exclusion zones for a picture
    """
    
    colors = ['red', 'blue', 'green', 'black', 'chocolate', 'deeppink', 'indigo', 'navy', 'olive', 'grey', 'crimson', 'blueviolet']
    template_name = "snapshotServer/excludeList.html"
    queryset = ExcludeZone.objects.none()
    
    def get_queryset(self):
        
        exclusion_list = []
        
        # get exclude zones from ref_snapshot
        exclusion_list += [(ex, ExclusionZoneListView.colors[i % len(ExclusionZoneListView.colors)], self.kwargs['ref_snapshot_id']) 
                for (i, ex) in enumerate(ExcludeZone.objects.filter(snapshot=self.kwargs['ref_snapshot_id']))]
        exclusion_list += [(ex, ExclusionZoneListView.colors[(i + len(exclusion_list)) % len(ExclusionZoneListView.colors)], self.kwargs['step_snapshot_id']) 
                for (i, ex) in enumerate(ExcludeZone.objects.filter(snapshot=self.kwargs['step_snapshot_id']))]
        
        return exclusion_list
        
        
    def get_context_data(self, **kwargs):
        context = super(ExclusionZoneListView, self).get_context_data(**kwargs)
        context['ref_snapshot_id'] = self.kwargs['ref_snapshot_id']
        context['step_snapshot_id'] = self.kwargs['step_snapshot_id']
        return context