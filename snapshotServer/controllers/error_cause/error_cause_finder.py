import logging
from django.conf import settings
from django.db import close_old_connections
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional

from . import Cause, ErrorCause, Reason
from .exception_error_cause_finder import ExceptionErrorCauseFinder
from .image_error_cause_finder import ImageErrorCauseFinder
from .js_error_cause_finder import JsErrorCauseFinder
from snapshotServer.models import TestCaseInSession, StepResult
from .network_error_cause_finder import NetworkErrorCauseFinder

logger = logging.getLogger(__name__)


class ErrorCauseFinderExecutor:

    # when using relatively slow instance (like ollama on mac), number of workers should be the same as number of ollama instances
    # on cloud services, this may be higher
    executor = None

    @classmethod
    def get_instance(cls):
        if not cls.executor:
            cls.executor = ThreadPoolExecutor(max_workers=settings.OPEN_WEBUI_WORKERS)

        return cls.executor

    @classmethod
    def submit(cls, test_case_in_session: TestCaseInSession):

        cls.get_instance().submit(ErrorCauseFinderExecutor.detect, test_case_in_session)

    @staticmethod
    def detect(test_case_in_session: TestCaseInSession):

        close_old_connections()
        error_cause_finder = ErrorCauseFinder(test_case_in_session)
        errors = sum([list(step_result.errors.all()) for step_result in StepResult.objects.filter(testCase=test_case_in_session, result=False).order_by('-pk')], [])

        for error in errors:
            error.cause = "analyzing ..."
            error.save()

        try:
            error_cause = error_cause_finder.detect_cause()
            if error_cause:
                for error in errors:
                    error.cause = error_cause.cause
                    error.causedBy = error_cause.why
                    error.causeDetails = error_cause.information if error_cause.information else ""
                    error.causeAnalysisErrors = '\n'.join(error_cause.analysis_errors)
                    error.save()
        except Exception as e:
            for error in errors:
                error.cause = "unknown"
                error.causedBy = "analysis_error"
                error.causeAnalysisErrors = f"Error detecting cause: {str(e)}"
                error.save()


class ErrorCauseFinder:
    """
    Class that tries to find what went wrong during the test
    """

    def __init__(self, test_case_in_session: Optional[TestCaseInSession],
                 js_error_cause_finder: Optional[JsErrorCauseFinder] = None,
                 image_error_cause_finder: Optional[ImageErrorCauseFinder] = None,
                 exception_error_cause_finder: Optional[ExceptionErrorCauseFinder] = None,
                 network_error_cause_finder: Optional[NetworkErrorCauseFinder] = None
                 ):

        self.test_case_in_session = test_case_in_session
        self.js_error_cause_finder = JsErrorCauseFinder(test_case_in_session) if js_error_cause_finder == None else js_error_cause_finder
        self.image_error_cause_finder = ImageErrorCauseFinder(test_case_in_session) if image_error_cause_finder == None else image_error_cause_finder
        self.exception_error_cause_finder = ExceptionErrorCauseFinder(test_case_in_session) if exception_error_cause_finder == None else exception_error_cause_finder
        self.network_error_cause_finder = NetworkErrorCauseFinder(test_case_in_session) if network_error_cause_finder == None else network_error_cause_finder

    def detect_cause(self) -> Optional[ErrorCause]:
        """
        Look for various causes
        """
        if self.test_case_in_session.isOkWithResult():
            return None

        analysis_errors = []

        assertion_error_analysis_details = self.exception_error_cause_finder.analyze_error()
        if assertion_error_analysis_details.analysis_error:
            analysis_errors.append("Assertions: " + assertion_error_analysis_details.analysis_error)
        if assertion_error_analysis_details.error_type == 'assertion' and assertion_error_analysis_details.location == 'step':
            return ErrorCause(Cause.APPLICATION, Reason.STEP_ASSERTION_ERROR, assertion_error_analysis_details.error_message, analysis_errors)
        elif assertion_error_analysis_details.error_type == 'assertion' and assertion_error_analysis_details.location == 'scenario':
            return ErrorCause(Cause.APPLICATION, Reason.SCENARIO_ASSERTION_ERROR, assertion_error_analysis_details.error_message, analysis_errors)
        elif assertion_error_analysis_details.location == 'scenario' or assertion_error_analysis_details.error_type == 'scenario':
            return ErrorCause(Cause.SCRIPT, Reason.SCENARIO_ERROR, assertion_error_analysis_details.error_message, analysis_errors)
        elif not assertion_error_analysis_details.search_cause:
            return ErrorCause(Cause.SCRIPT, Reason.UNKNOWN, assertion_error_analysis_details.error_message, analysis_errors)


        # check for error messages
        error_messages_analysis_details = self.image_error_cause_finder.is_error_message_displayed_in_last_step()
        if error_messages_analysis_details.analysis_error:
            analysis_errors.append("Error message: " + error_messages_analysis_details.analysis_error)

        if error_messages_analysis_details.details:
            return ErrorCause(Cause.APPLICATION, Reason.ERROR_MESSAGE, error_messages_analysis_details.details, analysis_errors)

        on_right_page_analysis_details = self.image_error_cause_finder.is_on_the_right_page()
        if on_right_page_analysis_details.analysis_error:
            analysis_errors.append("On same page: " + on_right_page_analysis_details.analysis_error)

        # in case analysis cannot be done, we assume we are on the right page
        if on_right_page_analysis_details.details:
            element_present_analysis_details = self.image_error_cause_finder.is_element_present_on_last_step()

            if element_present_analysis_details.analysis_error:
                analysis_errors.append("Element presence: " + element_present_analysis_details.analysis_error)

            if element_present_analysis_details.details:
                return ErrorCause(Cause.SCRIPT, Reason.BAD_LOCATOR, "Element seems to be present, check the locator", analysis_errors)
            else:
                return self.detect_other_causes(analysis_errors, "On right page: ")

        else:

            # check if we are on previous page
            on_previous_page_analysis_details = self.image_error_cause_finder.is_on_the_previous_page()
            if on_previous_page_analysis_details.analysis_error:
                analysis_errors.append("On previous page: " + on_previous_page_analysis_details.analysis_error)

            # why are we on previous page
            elif on_previous_page_analysis_details.details:
                return self.detect_other_causes(analysis_errors, "On previous page: ")

            # we are on an unknown page
            return ErrorCause(Cause.APPLICATION, Reason.UNKNOWN_PAGE, "Page is unknown", analysis_errors)

    def detect_other_causes(self, analysis_errors: list, prefix: str) -> ErrorCause:

        # JS error in console
        js_errors_analysis_details = self.js_error_cause_finder.has_javascript_errors()
        if js_errors_analysis_details.analysis_error:
            analysis_errors.append("JS error: " + js_errors_analysis_details.analysis_error)
        if js_errors_analysis_details.details:
            return ErrorCause(Cause.APPLICATION, Reason.JAVASCRIPT_ERROR, js_errors_analysis_details.details, analysis_errors)

        # Network error in HAR
        network_error_analysis_details = self.network_error_cause_finder.has_network_errors()
        if network_error_analysis_details.analysis_error:
            analysis_errors.append(network_error_analysis_details.analysis_error)
        elif network_error_analysis_details.details:
            return ErrorCause(Cause.APPLICATION, Reason.NETWORK_ERROR, prefix + "Consult HAR file", analysis_errors)

        network_latency_analysis_details = self.network_error_cause_finder.has_network_slowness()
        if network_latency_analysis_details.analysis_error:
            analysis_errors.append(network_latency_analysis_details.analysis_error)
        elif network_latency_analysis_details.details:
            return ErrorCause(Cause.ENVIRONMENT, Reason.NETWORK_SLOWNESS, prefix + "Consult HAR file", analysis_errors)

        return ErrorCause(Cause.UNKNOWN, Reason.UNKNOWN, None, analysis_errors)



