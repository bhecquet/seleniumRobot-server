'''
Created on 3 déc. 2024

@author: S047432
'''
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional
from django.views.generic.list import ListView
from snapshotServer.models import TestSession, TestCaseInSession
import json
from django.utils import timezone
from django.shortcuts import get_object_or_404

class TestSessionSummaryView(LoginRequiredMixinConditional, ListView):
    """
    View displaying a summary of tests executed during a test session
    This view will link to individual test results
    """
    
    template_name = "snapshotServer/testsSummary.html"
    colors = ['crimson', 'coral', 'dakrkhaki', 'darkorange', 'darkmagenta', 'dodgerblue', 
              'dimgrey', 'goldenrod', 'darkcyan', 'cyan', 'brown', 'olive', 'yellow',
              'sienna', 'darksalmon', 'darkslategrey']
      
    def get_queryset(self):
        
        timezone.now()
        
        session_id = self.kwargs['sessionId']
        test_case_in_session_data = {}
        badge_per_error = {None: {'id': -1, 'error_short': '', 'error': '', 'color': 'white'}}
        badge_index = 0
        
        for test_case_in_session in TestCaseInSession.objects.filter(session = session_id).order_by("date"):
            step_results = test_case_in_session.stepresult.all()
            
            error = self.get_error_in_test(test_case_in_session.stepresult.all())
            error_str = None
            
            if error:
                error_str = str(error)
                if error_str not in badge_per_error.keys():
                    badge_per_error[error_str] = {'id': badge_index, 'error_short': error.action.split('>')[0], 'error': error_str, 'color': self.colors[badge_index % len(self.colors)]}
                    badge_index += 1

            
            
            test_case_in_session_data[test_case_in_session] = (
                        test_case_in_session.isOkWithSnapshots(),                                   # no problem with snapshot comparison
                        len(test_case_in_session.stepresult.all()),                                 # number of steps
                        len([sr for sr in step_results if not sr.result]),                          # number of failed steps
                        int(test_case_in_session.duration() / 1000),                                # duration
                        self.get_related_errors_in_test(step_results),                              # number of tests with the same error
                        badge_per_error[error_str],                                                 # info that will display on badge
                        {info.name: json.loads(info.info) for info in test_case_in_session.testInfos.all()} # test infos
                   )

        return test_case_in_session_data
            
    def get_related_errors_in_test(self, step_results):
        error = self.get_error_in_test(step_results)
        
        if error:
            # relatedErrors contains the error itself its related, so remove our error
            return [e.stepResult.testCase for e in error.relatedErrors.exclude(id=error.id)]
        else:
            return []
        
    def get_error_in_test(self, step_results):
        """
        Returns the error that caused the test (the first one)
        """
        steps_in_error = [sr for sr in step_results if not sr.result][0:1]
        if steps_in_error:
            errors = steps_in_error[0].errors.all()
            return errors[0] if errors else None
        else:
            return None
        
    def get_target_application(self):
        test_session = TestSession.objects.get(id=self.kwargs['sessionId'])
        return test_session.version.application
            
    def get_context_data(self, **kwargs):
        
        context = super(TestSessionSummaryView, self).get_context_data(**kwargs)
        
        session_id = self.kwargs['sessionId']
        context['testSession'] = get_object_or_404(TestSession, id=session_id)
        context['testInfoList'] = []
        
        for test_case_in_session in context['testSession'].testcaseinsession_set.all():
            for test_info in test_case_in_session.testInfos.all():
                if test_info.name not in context['testInfoList']:
                    context['testInfoList'].append(test_info.name)

        return context

    