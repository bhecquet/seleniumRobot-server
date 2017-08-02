'''
Created on 26 juil. 2017

@author: worm
'''
import pickle

from django.views.generic.base import TemplateView

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestCaseInSession, TestSession


class PictureView(TemplateView):
    template_name = "snapshotServer/displayPanel.html"

    def get_context_data(self, **kwargs):
        """
        Look for the snapshot of our session
        @param sessionId
        @param testCaseId    a TestCaseInSession object id
        @param testStepId    a TestStep object id
        """
        context = super(PictureView, self).get_context_data(**kwargs)
        
        stepSnapshot = Snapshot.objects.filter(stepResult__testCase=self.kwargs['testCaseInSessionId'], 
                                               stepResult__step=self.kwargs['testStepId']).last()
        
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
                    # search with the same test case name and same step name on the same application version so that comparison
                    # is done on same basis
                    # TODO: reference could be searched in previous versions
                    testCase = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
                    refSnapshots = Snapshot.objects.filter(stepResult__testCase__testCase__name=testCase.testCase.name) \
                                                .filter(stepResult__testCase__session__version=testCase.session.version) \
                                                .filter(stepResult__step=self.kwargs['testStepId']) \
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
        context['testCaseId'] = self.kwargs['testCaseInSessionId']
        context['testStepId'] = self.kwargs['testStepId']
        return context