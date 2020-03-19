'''
Created on 26 juil. 2017

@author: worm
'''
import pickle

from django.views.generic.base import TemplateView

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestCaseInSession, TestSession
import base64


class PictureView(TemplateView):
    """
    View displaying the comparison between pictures (the current and the reference)
    """
    
    template_name = "snapshotServer/displayPanel.html"

    def get_context_data(self, **kwargs):
        """
        Look for the snapshot of our session
        @param sessionId
        @param testCaseId    a TestCaseInSession object id
        @param testStepId    a TestStep object id
        """
        context = super(PictureView, self).get_context_data(**kwargs)
        context['captureList'] = []
        context['testCaseId'] = self.kwargs['testCaseInSessionId']
        context['testStepId'] = self.kwargs['testStepId']
        
        stepSnapshots = Snapshot.objects.filter(stepResult__testCase=self.kwargs['testCaseInSessionId'], 
                                               stepResult__step=self.kwargs['testStepId'])
        
        for stepSnapshot in stepSnapshots:
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
                        # search with the same test case name / same step name / same application version / same image name so that comparison
                        # is done on same basis
                        # TODO: reference could be searched in previous versions
                        testCase = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
                        refSnapshots = Snapshot.objects.filter(stepResult__testCase__testCase__name=testCase.testCase.name, 
                                                               stepResult__testCase__session__version=testCase.session.version,
                                                               stepResult__step=self.kwargs['testStepId'], 
                                                               refSnapshot=None,
                                                               id__lt=stepSnapshot.id,
                                                               name=stepSnapshot.name)
                         
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
                    diffPicture = base64.b64encode(DiffComputer.markDiff(stepSnapshot.image.width, stepSnapshot.image.height, diffPixels)).decode('ascii')
                    
                else:
                    diffPixels = []
                    diffPicture = None
                    
            # not snapshot has been recorded for this session
            else:
                refSnapshot = None
                diffPixels = []
                diffPicture = None
                
            stepSnapshotContext = {
                'name': stepSnapshot.name,
                'reference': refSnapshot,
                'stepSnapshot': stepSnapshot,
                'diffB64': diffPicture
                }
            context['captureList'].append(stepSnapshotContext)
            
        return context
    
                