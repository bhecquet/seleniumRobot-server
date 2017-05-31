'''
Created on 4 mai 2017

@author: bhecquet
'''

from django.views.generic import ListView
from snapshotServer.models import TestSession, TestCase, Snapshot, ExcludeZone
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View
import pickle
from snapshotServer.controllers.DiffComputer import DiffComputer

class SessionList(ListView):
    model = TestSession
    template_name = "snapshotServer/compare.html"
    
class TestList(ListView):
    template_name = "snapshotServer/testList.html"
    
    def get_queryset(self):
        return TestCase.objects.filter(testsession=self.args[0])
    
    def get_context_data(self, **kwargs):
        context = super(TestList, self).get_context_data(**kwargs)
        context['sessionId'] = self.args[0]
        return context
    
class StepList(ListView):
    template_name = "snapshotServer/stepList.html"
    
    def get_queryset(self):
        try:
            return TestCase.objects.get(id=self.args[1]).testSteps.all()
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(StepList, self).get_context_data(**kwargs)
        context['testCaseId'] = self.args[1]
        context['sessionId'] = self.args[0]
        return context
    
class PictureView(TemplateView):
    template_name = "snapshotServer/displayPanel.html"

    def get_context_data(self, **kwargs):
        """
        Look for the snapshot of our session
        """
        context = super(PictureView, self).get_context_data(**kwargs)
        
        stepSnapshot = Snapshot.objects.filter(session=self.args[0]).filter(testCase=self.args[1]).filter(step=self.args[2]).last()
        
        
        if stepSnapshot:

            if 'makeRef' in self.request.GET: 
                if self.request.GET['makeRef'] == 'True' and stepSnapshot.refSnapshot is not None:
                    previousSnapshot = stepSnapshot.refSnapshot
                    stepSnapshot.refSnapshot = None
                    stepSnapshot.pixelsDiff = None
                    stepSnapshot.save()
                    
                    # Compute differences for the following snapshots as they will depend on this new ref
                    for snap in stepSnapshot.snapshotsUntilNextRef(previousSnapshot):
                        DiffComputer.addJobs(stepSnapshot, snap)
                    
                elif self.request.GET['makeRef'] == 'False' and stepSnapshot.refSnapshot is None:
                    # search a reference with a lower id, meaning that it has been recorded before our step
                    refSnapshots = Snapshot.objects.filter(testCase=self.args[1]) \
                                                .filter(step=self.args[2]) \
                                                .filter(refSnapshot=None) \
                                                .filter(id__lt=stepSnapshot.id)
                    
                    # do not remove reference flag if our snapshot is the very first one
                    if len(refSnapshots) > 0:
                        stepSnapshot.refSnapshot = refSnapshots.last()
                        stepSnapshot.save()
                        
                        # recompute diff pixels
                        DiffComputer.computeNow(stepSnapshot.refSnapshot, stepSnapshot)
                        
                        # recompute all following snapshot as they will depend on a previous ref
                        for snap in stepSnapshot.snapshotsUntilNextRef(stepSnapshot):
                            DiffComputer.addJobs(stepSnapshot.refSnapshot, snap)
    
            refSnapshot = stepSnapshot.refSnapshot
            
            # extract difference pixel. Recompute in case this step is no more a reference
            diffPixelsBin = stepSnapshot.pixelsDiff
                
            if diffPixelsBin:
                diffPixels = pickle.loads(diffPixelsBin)
            else:
                diffPixels = []
                
        # not snapshot has been recorded for this session
        else:
            refSnapshot = None
            diffPixels = []
         
        context['reference'] = refSnapshot
        context['stepSnapshot'] = stepSnapshot
        context['diff'] = str([[p.x, p.y] for p in diffPixels])
        context['testCaseId'] = self.args[1]
        context['sessionId'] = self.args[0]
        context['testStepId'] = self.args[2]
        return context
    
class ExclusionZoneList(ListView):
    template_name = "snapshotServer/excludeList.html"
    
    def get_queryset(self):
        return ExcludeZone.objects.filter(snapshot=self.args[0])

