'''
Created on 26 juil. 2017

@author: worm
'''
import pickle

from django.views.generic.base import TemplateView

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestCaseInSession, TestSession
import base64
import sys


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
        
        step_snapshots = Snapshot.objects.filter(stepResult__testCase=self.kwargs['testCaseInSessionId'], 
                                               stepResult__step=self.kwargs['testStepId'])
        
        for step_snapshot in step_snapshots:
            if step_snapshot:
    
                # request should contain the snapshotId when makeRef is sent. Filter on it
                if 'makeRef' in self.request.GET and 'snapshotId' in self.request.GET and int(self.request.GET['snapshotId']) == step_snapshot.id:

                    if self.request.GET['makeRef'] == 'True' and step_snapshot.refSnapshot is not None:
                        previous_snapshot = step_snapshot.refSnapshot
                        step_snapshot.refSnapshot = None
                        step_snapshot.pixelsDiff = None
                        step_snapshot.save()
                        
                        # Compute differences for the following snapshots as they will depend on this new ref
                        for snap in step_snapshot.snapshotsUntilNextRef(previous_snapshot):
                            DiffComputer.addJobs(step_snapshot, snap)
                        
                    elif self.request.GET['makeRef'] == 'False' and step_snapshot.refSnapshot is None:
                        # search a reference with a lower id, meaning that it has been recorded before our step
                        # search with the same test case name / same step name / same application version / same image name so that comparison
                        # is done on same basis
                        # TODO: reference could be searched in previous versions
                        test_case = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
                        ref_snapshots = Snapshot.objects.filter(stepResult__testCase__testCase__name=test_case.testCase.name, 
                                                               stepResult__testCase__session__version=test_case.session.version,
                                                               stepResult__step=self.kwargs['testStepId'], 
                                                               refSnapshot=None,
                                                               id__lt=step_snapshot.id,
                                                               name=step_snapshot.name)
                         
                        # do not remove reference flag if our snapshot is the very first one
                        if len(ref_snapshots) > 0:
                            step_snapshot.refSnapshot = ref_snapshots.last()
                            step_snapshot.save()
                            
                            # recompute diff pixels
                            DiffComputer.computeNow(step_snapshot.refSnapshot, step_snapshot)
                            
                            # recompute all following snapshot as they will depend on a previous ref
                            for snap in step_snapshot.snapshotsUntilNextRef(step_snapshot):
                                DiffComputer.addJobs(step_snapshot.refSnapshot, snap)
        
                ref_snapshot = step_snapshot.refSnapshot
                
                # extract difference pixel. Recompute in case this step is no more a reference
                diff_pixels_bin = step_snapshot.pixelsDiff
                print(sys.getsizeof(diff_pixels_bin))
                    
                if diff_pixels_bin:
                    try:
                        diff_pixels = pickle.loads(diff_pixels_bin)
                        diff_picture = base64.b64encode(DiffComputer.markDiff(step_snapshot.image.width, step_snapshot.image.height, diff_pixels)).decode('ascii')
                    except:
                        diff_picture = base64.b64encode(diff_pixels_bin).decode('ascii')
                else:
                    diff_pixels = []
                    diff_picture = None
                    
            # not snapshot has been recorded for this session
            else:
                ref_snapshot = None
                diff_pixels = []
                diff_picture = None
                
            step_snapshot_context = {
                'name': step_snapshot.name,
                'reference': ref_snapshot,
                'stepSnapshot': step_snapshot,
                'diffB64': diff_picture
                }
            context['captureList'].append(step_snapshot_context)
            
        return context
    
                