'''
Created on 26 juil. 2017

@author: worm
'''
import pickle

from django.views.generic.base import TemplateView

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestCaseInSession, TestSession, \
    TestStep, ExcludeZone
import base64
import sys
import io
from PIL import Image
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional
import os
from django.conf import settings


class PictureView(LoginRequiredMixinConditional, TemplateView):
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
        
        step = TestStep.objects.get(pk=self.kwargs['testStepId'])
        

        context['status'] = step.isOkWithSnapshots(self.kwargs['testCaseInSessionId'])
        
        # check that the user has permissions to edit exclusion zones. If not buttons will be disabled
        authenticated_to_edit = not self.security_api_enabled or (self.security_api_enabled and self.request.user.is_authenticated)
        allowed_to_edit = not self.security_enabled or (self.security_enabled and self.request.user.has_perms(['snapshotServer.add_excludezone', 'snapshotServer.change_excludezone', 'snapshotServer.delete_excludezone']))
        
        context['editable'] = authenticated_to_edit and allowed_to_edit
        if context['editable']:
            context['editButtonText'] = 'Edit'
        elif not authenticated_to_edit:
            context['editButtonText'] = 'You must log in to edit.'
        elif not allowed_to_edit:
            context['editButtonText'] = "You don't have right to edit"
        
        step_snapshots = Snapshot.objects.filter(stepResult__testCase=self.kwargs['testCaseInSessionId'],
                                               stepResult__step=self.kwargs['testStepId']).order_by('id')
        
        for step_snapshot in step_snapshots:
            if step_snapshot:
    
                # request should contain the snapshotId when makeRef is sent. Filter on it
                if 'makeRef' in self.request.GET and 'snapshotId' in self.request.GET and int(self.request.GET['snapshotId']) == step_snapshot.id and context['editable']:

                    if self.request.GET['makeRef'] == 'True' and step_snapshot.refSnapshot is not None:
                        previous_snapshot = step_snapshot.refSnapshot
                        step_snapshot.refSnapshot = None
                        step_snapshot.pixelsDiff = None
                        step_snapshot.save()
                        
                        # copy exclude zones to the new ref so that they may be processed independently
                        for exclude_zone in ExcludeZone.objects.filter(snapshot=previous_snapshot):
                            exclude_zone.copy_to_snapshot(step_snapshot)
                        
                        # Compute differences for the following snapshots as they will depend on this new ref
                        for snap in step_snapshot.snapshotsUntilNextRef(previous_snapshot):
                            DiffComputer.get_instance().add_jobs(step_snapshot, snap)
                            
                    elif self.request.GET['makeRef'] == 'False' and step_snapshot.refSnapshot is None:
                        # search a reference with a lower id, meaning that it has been recorded before our step
                        # search with the same test case name / same step name / same application version / same environment / same browser / same image name so that comparison
                        # is done on same basis
                        # TODO: reference could be searched in previous versions
                        test_case = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
                        ref_snapshots = Snapshot.objects.filter(stepResult__testCase__testCase__name=test_case.testCase.name,
                                                               stepResult__testCase__session__version=test_case.session.version,
                                                               stepResult__testCase__session__environment=test_case.session.environment,
                                                               stepResult__testCase__session__browser=test_case.session.browser,
                                                               stepResult__step=self.kwargs['testStepId'],
                                                               refSnapshot=None,
                                                               id__lt=step_snapshot.id,
                                                               name=step_snapshot.name)
                         
                        # do not remove reference flag if our snapshot is the very first one
                        if len(ref_snapshots) > 0:
                            step_snapshot.refSnapshot = ref_snapshots.last()
                            step_snapshot.save()
                            
                            diff_computer = DiffComputer.get_instance()
                            
                            # recompute diff pixels
                            diff_computer.compute_now(step_snapshot.refSnapshot, step_snapshot)
                            
                            # recompute all following snapshot as they will depend on a previous ref
                            for snap in step_snapshot.snapshotsUntilNextRef(step_snapshot):
                                diff_computer.add_jobs(step_snapshot.refSnapshot, snap)
        
                ref_snapshot = step_snapshot.refSnapshot
                
                # extract difference pixel. Recompute in case this step is no more a reference
                diff_pixels_bin = step_snapshot.pixelsDiff
                
                if os.path.isfile(settings.MEDIA_ROOT + os.sep + step_snapshot.image.name):
                    snapshot_width = step_snapshot.image.width
                    snapshot_height = step_snapshot.image.height
                else:
                    snapshot_height = 0
                    snapshot_width = 0
                
                if diff_pixels_bin and snapshot_width and snapshot_height:
                    try:
                        diff_pixels = pickle.loads(diff_pixels_bin)
                        diff_picture = base64.b64encode(DiffComputer.get_instance().mark_diff(step_snapshot.image.width, step_snapshot.image.height, diff_pixels)).decode('ascii')
                        diff_pixels_percentage = 0.0
                    except Exception:
#                         diff_picture_bin
                        diff_picture = base64.b64encode(diff_pixels_bin).decode('ascii')
                        with io.BytesIO(diff_pixels_bin) as input:
                            diff_pixels_percentage = 100 * (sum(list(Image.open(input).getdata(3))) / 255) / (step_snapshot.image.width * step_snapshot.image.height)
                            
                else:
                    diff_pixels = []
                    diff_picture = None
                    diff_pixels_percentage = 0.0
                    
            # not snapshot has been recorded for this session
            else:
                ref_snapshot = None
                diff_pixels = []
                diff_picture = None
                diff_pixels_percentage = 0.0
                
            step_snapshot_context = {
                'name': step_snapshot.name,
                'reference': ref_snapshot,
                'stepSnapshot': step_snapshot,
                'width': snapshot_width,
                'height': snapshot_height,
                'diffB64': diff_picture,
                'diffPercentage': diff_pixels_percentage
                }
            context['captureList'].append(step_snapshot_context)
            
        
            
        context['enable'] = True # do we display the block  
        if self.request.path.endswith('noheader/'):
            if not context['captureList']:
                context['enable'] = False
            context['testStepName'] = "Snapshot comparison"
        else:
            context['testStepName'] = step.name
            
            
        return context
                
