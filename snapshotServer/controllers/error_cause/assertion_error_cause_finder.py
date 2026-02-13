import json

from . import AnalysisDetails
from ...models import StepResult, TestStep, Error


class AssertionErrorCauseFinder:

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session

    def is_assertion_error(self) -> AnalysisDetails:
        """
        Look in failed step and test case if exception is AssertionError
        In this case, no need to try to detect the cause
        :return an AnalysisDetails with [<is_assertionError>, <step/scenario>, <exceptionMessage>] as details
        """
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
        if len(failed_step_result) > 0:
            errors = Error.objects.filter(stepResult = failed_step_result[0])
            if errors:
                error = errors[0]
                if "AssertionError" in error.exception:
                    return AnalysisDetails([True, 'step', error.errorMessage], None)
                else:
                    return AnalysisDetails([False, 'step', error.errorMessage], None)
            else:
                return AnalysisDetails([False, 'step', None], None)
        else:
            # no step failed, so error is in script, which does something incorrectly
            try:
                stacktrace = json.loads(self.test_case_in_session.stacktrace)
                if "AssertionError" in stacktrace.get("stacktrace", ""):
                    return AnalysisDetails([True, 'scenario', stacktrace['stacktrace'].split('\n')[0]], None)
                else:
                    return AnalysisDetails([False, 'scenario', stacktrace['stacktrace'].split('\n')[0]], None)
            except Exception as e:
                return AnalysisDetails([False, "scenario", None], "Error reading test case logs: " + str(e))