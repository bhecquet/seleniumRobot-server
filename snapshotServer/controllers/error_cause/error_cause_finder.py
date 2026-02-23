import logging
import threading
from collections import namedtuple
from typing import Optional

from .assertion_error_cause_finder import AssertionErrorCauseFinder
from .image_error_cause_finder import ImageErrorCauseFinder
from .js_error_cause_finder import JsErrorCauseFinder
from snapshotServer.models import TestCaseInSession, StepResult, File, StepReference, TestStep, Error
from .network_error_cause_finder import NetworkErrorCauseFinder

ErrorCause = namedtuple("ErrorCause", [
                                        'cause',        # the probable cause of the error (application, scripting, tool, environment
                                       'why',           # what guided us to the probable cause (error message, JS errors, missing field, ...)
                                       'information',    # additional information related to "why"
                                        'analysis_errors' # list of error messages during analysis
])


logger = logging.getLogger(__name__)


class ErrorCauseFinderThread(threading.Thread):

    def __init__(self, test_case_in_session):
        """
        Init computer thread
        :param test_case_in_session     the test case in session
        """
        super().__init__()
        self.test_case_in_session = test_case_in_session
        self.error_cause_finder = ErrorCauseFinder(self.test_case_in_session)
        print(self.error_cause_finder)

    def run(self):

        errors = sum([list(step_result.errors.all()) for step_result in StepResult.objects.filter(testCase=self.test_case_in_session, result=False).order_by('-pk')], [])

        for error in errors:
            error.cause = "analyzing ..."
            error.save()

        try:
            error_cause = self.error_cause_finder.detect_cause()
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
                assertion_error_cause_finder: Optional[AssertionErrorCauseFinder] = None,
                network_error_cause_finder: Optional[NetworkErrorCauseFinder] = None
                 ):

        self.test_case_in_session = test_case_in_session
        self.js_error_cause_finder = JsErrorCauseFinder(test_case_in_session) if js_error_cause_finder == None else js_error_cause_finder
        self.image_error_cause_finder = ImageErrorCauseFinder(test_case_in_session) if image_error_cause_finder == None else image_error_cause_finder
        self.assertion_error_cause_finder = AssertionErrorCauseFinder(test_case_in_session) if assertion_error_cause_finder == None else assertion_error_cause_finder
        self.network_error_cause_finder = NetworkErrorCauseFinder(test_case_in_session) if network_error_cause_finder == None else network_error_cause_finder

    def detect_cause(self) -> Optional[ErrorCause]:
        """
        Look for various causes
        """
        if self.test_case_in_session.isOkWithResult():
            return None

        analysis_errors = []

        assertion_error_analysis_details = self.assertion_error_cause_finder.is_assertion_error()
        if assertion_error_analysis_details.analysis_error:
            analysis_errors.append("Assertions: " + assertion_error_analysis_details.analysis_error)
        elif assertion_error_analysis_details.details[0]:
            return ErrorCause("application", "assertion on " + assertion_error_analysis_details.details[1], assertion_error_analysis_details.details[2], analysis_errors)
        elif assertion_error_analysis_details.details[1] == 'scenario':
            return ErrorCause("script", "error in scenario", assertion_error_analysis_details.details[2], analysis_errors)

        # check for error messages
        error_messages_analysis_details = self.image_error_cause_finder.is_error_message_displayed_in_last_step()
        if error_messages_analysis_details.analysis_error:
            analysis_errors.append("Error message: " + error_messages_analysis_details.analysis_error)

        if error_messages_analysis_details.details:
            return ErrorCause("application_error", "error_message", error_messages_analysis_details.details, analysis_errors)

        on_right_page_analysis_details = self.image_error_cause_finder.is_on_the_right_page()
        if on_right_page_analysis_details.analysis_error:
            analysis_errors.append("On same page: " + on_right_page_analysis_details.analysis_error)

        # in case analysis cannot be done, we assume we are on the right page
        if on_right_page_analysis_details.details:
            element_present_analysis_details = self.image_error_cause_finder.is_element_present_on_last_step()

            if element_present_analysis_details.analysis_error:
                analysis_errors.append("Element presence: " + element_present_analysis_details.analysis_error)

            if element_present_analysis_details.details:
                # TODO: send the DOM and the image to the LLM
                return ErrorCause("script", "bad_locator", "Element seems to be present, check the locator", analysis_errors)
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
            return ErrorCause("application_change", "unknown_page", "Page is unknown", analysis_errors)

    def detect_other_causes(self, analysis_errors: list, prefix: str) -> ErrorCause:

        # JS error in console
        js_errors_analysis_details = self.js_error_cause_finder.has_javascript_errors()
        if js_errors_analysis_details.analysis_error:
            analysis_errors.append("JS error: " + js_errors_analysis_details.analysis_error)
        if js_errors_analysis_details.details:
            return ErrorCause("application_error", "javascript_error", js_errors_analysis_details.details, analysis_errors)

        # Network error in HAR
        network_error_analysis_details = self.network_error_cause_finder.has_network_errors()
        if network_error_analysis_details.analysis_error:
            analysis_errors.append(network_error_analysis_details.analysis_error)
        elif network_error_analysis_details.details:
            return ErrorCause("application_error", "network_error", prefix + "Consult HAR file", analysis_errors)

        network_latency_analysis_details = self.network_error_cause_finder.has_network_slowness()
        if network_latency_analysis_details.analysis_error:
            analysis_errors.append(network_latency_analysis_details.analysis_error)
        elif network_latency_analysis_details.details:
            return ErrorCause("environment", "network_slowness", prefix + "Consult HAR file", analysis_errors)

        return ErrorCause("script", "unknown", None, analysis_errors)



