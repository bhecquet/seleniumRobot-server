'''
Created on 4 sept. 2017

@author: worm
'''

from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from snapshotServer.models import TestCaseInSession, StepResult, Snapshot, Error
import json
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional
from snapshotServer.controllers.error_cause.knowledge_base_analyzer import find_probable_cause


class TestResultView(LoginRequiredMixinConditional, ListView):
    """
    View displaying a single test result
    """

    template_name = "snapshotServer/testResult.html"

    def get_queryset(self):
        try:
            test_case_in_session = self.kwargs['test_case_in_session_id']
            current_test = TestCaseInSession.objects.get(id=test_case_in_session)
            test_steps = current_test.testSteps.all()

            step_snapshots = {}

            for step_result in StepResult.objects.filter(
                    testCase=test_case_in_session,
                    step__in=test_steps
            ).order_by('id'):



                try:
                    details = json.loads(step_result.stacktrace)

                except Exception as e:

                    details = {}

                step_result.details = details
                step_result.details["suggestedCause"] = "TEST AFFICHAGE"
                # EXPLOITATION BASE DE CONNAISSANCE
                if "exception" in step_result.details:
                    try:
                        result = find_probable_cause(
                            exception=step_result.details.get("exception"),
                            testCase=step_result.testCase.testCase if hasattr(step_result, 'testCase') else None,
                            testStep=step_result.step if hasattr(step_result, 'step') else None
                        )

                        if result:
                            step_result.details["suggestedCause"] = result["cause"]
                            step_result.details["confidence"] = int(
                                (result["count"] / result["total"]) * 100
                            )

                    except Exception as e:
                        print(" ERROR in find_probable_cause:", e)

                # snapshots
                try:
                    step_snapshots[step_result] = list(
                        Snapshot.objects.filter(stepResult=step_result)
                    )
                except Exception as e:

                    step_snapshots[step_result] = None

            return step_snapshots

        except Exception as e:

            return {}

    def get_context_data(self, **kwargs):
        context = super(TestResultView, self).get_context_data(**kwargs)
        current_test = get_object_or_404(
            TestCaseInSession,
            pk=self.kwargs['test_case_in_session_id']
        )

        context['currentTest'] = current_test
        context['session'] = current_test.session
        context['testCaseId'] = self.kwargs['test_case_in_session_id']
        context['snasphotComparisonResult'] = current_test.isOkWithSnapshots()
        context['status'] = current_test.status

        # in case of computing error, do not display a step dedicated to it
        if context['snasphotComparisonResult'] is None:
            context['currentTest'].session.compareSnapshot = False

        # change test result when requested by the test
        if (
                current_test.session.compareSnapshot
                and current_test.session.compareSnapshotBehaviour == 'CHANGE_TEST_RESULT'
                and context['snasphotComparisonResult'] is False
        ):
            context['status'] = 'FAILURE'

        context['browserOrApp'] = current_test.session.browser.split(':')[-1].capitalize()
        context['applicationType'] = current_test.session.browser.split(':')[0].capitalize()

        try:
            stack_and_logs = json.loads(context['currentTest'].stacktrace)
            context['stacktrace'] = stack_and_logs['stacktrace'].split('\n')
            context['logs'] = stack_and_logs['logs'].split('\n')
        except Exception:
            context['stacktrace'] = []
            context['logs'] = ['no logs available']

        last_step = [s for s in current_test.testSteps.all() if s.name == 'Test end']
        if last_step:
            last_step_result = StepResult.objects.filter(
                testCase=current_test,
                step__in=last_step
            )
            try:
                context['lastStepDetails'] = json.loads(last_step_result[0].stacktrace)
            except Exception:
                context['lastStepDetails'] = {}

        context['infos'] = {}
        for test_info in current_test.testInfos.all():
            try:
                context['infos'][test_info.name] = json.loads(test_info.info)
            except Exception:
                pass

        errors = Error.objects.filter(
            stepResult__in=StepResult.objects.filter(testCase=current_test)
        )
        for i, error in enumerate(errors):
            context['infos']['caused details_' + str(i)] = {
                "type": "errorcause",
                "info": error.friendly_message,
                "errors": error.causeAnalysisErrors if error.causeAnalysisErrors else 'No error'
            }

        return context

    def get_target_application(self):
        test_case_in_session = TestCaseInSession.objects.get(
            id=self.kwargs['test_case_in_session_id']
        )
        return test_case_in_session.session.version.application