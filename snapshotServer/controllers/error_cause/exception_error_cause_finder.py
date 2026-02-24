import json
from typing import Optional

from . import AnalysisDetails
from ...models import StepResult, TestStep, Error

class ExceptionAnalysisDetails:

    def __init__(self, search_cause: bool, location: str, error_type: str, error_message: str, analysis_error: Optional[str]):
        self.search_cause = search_cause
        self.location = location # 'step', 'scenario'
        self.error_type = error_type
        self.error_message = error_message
        self.analysis_error = analysis_error

class ExceptionErrorCauseFinder:

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session
        self.failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
        self.errors = []
        if len(self.failed_step_result) > 0:
            self.errors = Error.objects.filter(stepResult = self.failed_step_result[0])

    def analyze_error(self) -> ExceptionAnalysisDetails:
        """
        Look in failed step and test case if exception is AssertionError
        In this case, no need to try to detect the cause
        :return an AnalysisDetails with [<is_assertionError>, <step/scenario>, <exceptionMessage>] as details
        """

        if len(self.failed_step_result) > 0:
            if self.errors:
                error = self.errors[0]
                if "AssertionError" in error.exception:
                    return ExceptionAnalysisDetails(False, 'step', 'assertion', error.errorMessage, None)
                elif "NoSuchElementException" in error.exception or "NotCurrentPageException" in error.exception or "ImageSearchException" in error.exception:
                    return ExceptionAnalysisDetails(True, 'step', 'search_element', error.errorMessage, None)
                elif "ScenarioException" in error.exception:
                    return ExceptionAnalysisDetails(False, 'step', 'scenario', error.errorMessage, None)
                else:
                    return ExceptionAnalysisDetails(False, 'step', 'exception', error.errorMessage, None)
            else:
                return ExceptionAnalysisDetails(False, 'step', 'unknown', '', None)
        else:
            # no step failed, so error is in script, which does something incorrectly
            try:
                stacktrace = json.loads(self.test_case_in_session.stacktrace)
                if "AssertionError" in stacktrace.get("stacktrace", ""):
                    return ExceptionAnalysisDetails(False, 'scenario', 'assertion', stacktrace['stacktrace'].split('\n')[0], None)
                elif "ScenarioException" in stacktrace.get("stacktrace", ""):
                    return ExceptionAnalysisDetails(False, 'scenario', 'scenario', stacktrace['stacktrace'].split('\n')[0], None)
                else:
                    return ExceptionAnalysisDetails(False, 'scenario', 'unknown', stacktrace['stacktrace'].split('\n')[0], None)
            except Exception as e:
                return ExceptionAnalysisDetails(False, "scenario", 'unknown', '', "Error reading test case logs: " + str(e))

