import json
import logging
import os
from collections import namedtuple
from typing import Optional

from django.conf import settings

from snapshotServer.controllers.llm_connector import LlmConnector
from snapshotServer.models import TestCaseInSession, StepResult, File, StepReference, TestStep

ErrorCause = namedtuple("ErrorCause", [
                                        'cause',        # the probable cause of the error (application, scripting, tool, environment
                                       'why',           # what guided us to the probable cause (error message, JS errors, missing field, ...)
                                       'information'    # additional information related to "why"
])

AnalysisDetails = namedtuple('AnalysisDetails', [
    'details',
    'analysis_error'])

logger = logging.getLogger(__name__)

class ErrorCauseFinder:
    """
    Class that tries to find what went wrong during the test
    """

    def __init__(self, test_case_in_session: Optional[TestCaseInSession]):

        self.test_case_in_session = test_case_in_session
        self.llm_connector = LlmConnector()

    def detect_cause(self):
        """
        Look for various causes
        """
        if self.test_case_in_session.isOkWithResult():
            return None

        same_page, analysis_error = self.is_on_the_right_page()
        if same_page:
            # TODO: do something with analysis errors
            if self.is_element_present_on_page():
                # TODO: send the DOM and the image to the LLM
                return ErrorCause("script", "bad_locator", None)
            js_errors = self.has_javascript_errors()
            if js_errors:
                return ErrorCause("application_error", "javascript_error", js_errors)
            if self.has_network_errors():
                return ErrorCause("application_error", "network_error", "Consult HAR file")
            elif self.has_network_slowness():
                return ErrorCause("environment", "network_slowness", "Consult HAR file")
            else:
                return ErrorCause("script", "unknown", None)

        else:
            error_messages, analysis_error = self.is_error_message_displayed()
            if error_messages:
                # TODO: do something with analysis errors
                return ErrorCause("application_error", "error_message", error_messages)
            elif self.is_on_the_previous_page():
                if self.has_network_errors():
                    return ErrorCause("application_error", "network_error", "Consult HAR file")
                elif self.has_network_slowness():
                    return ErrorCause("environment", "network_slowness", "Consult HAR file")
                else:
                    return ErrorCause("application", "bad_behaviour", "Consult Video")
            else:
                return ErrorCause("application_change", "right_page", None)


    def is_on_the_right_page(self):
        """
        Check whether test was on the right page when error occurred
        :return: [true/false, <analysis error if any>] if test is on the right page
        """
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).order_by('-pk')
        if len(failed_step_result) > 0:
            return self._is_step_on_same_page(failed_step_result[0], failed_step_result[0])

        return True, "No image to compare"


    def is_on_the_previous_page(self):
        """
        If we are not on the right page, we may be on the previous page which means that a previous click did not produce the expected action
        :return:
        """
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).order_by('-pk')
        previous_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, pk_lt=failed_step_result.id).order_by('-pk')
        if len(failed_step_result) > 0 and len(previous_step_result) > 0:
            return self._is_step_on_same_page(previous_step_result[0], failed_step_result[0])

        return True, "No image to compare"

    def is_step_on_same_page(self, step_for_reference_result: StepResult, failed_step_result: StepResult) -> AnalysisDetails:
        """
        returns the result of comparison between the image the failed step and a reference image that will be taken from a previous step
        :param step_for_reference_result:
        :param failed_step_result:
        :return:
        """
        step_reference = StepReference.objects.filter(testCase=self.test_case_in_session.testCase,
                                                      environment=self.test_case_in_session.session.environment,
                                                      version=self.test_case_in_session.session.version,
                                                      testStep=step_for_reference_result.step)

        if len(step_reference) == 0 or not step_reference[0].image or os.path.isfile(step_reference[0].image.file.path):
            return AnalysisDetails(True, f"No reference image for step '{failed_step_result.step.name}' in test case '{self.test_case_in_session.testCase.name}'")

        try:
            # load details
            step_result_details = json.loads(failed_step_result.stacktrace)
            for snapshot in step_result_details['snapshots']:
                if snapshot['idImage'] and snapshot['snapshotCheckType'] == 'NONE_REFERENCE':
                    image_file = File.objects.get(pk=snapshot['idImage'])
                    return self.is_on_same_page(step_reference[0].image.file.path, image_file.file.path)


        except Exception as e:
            return AnalysisDetails(True, f"Error reading file for analysis: {str(e)}")

    def is_on_same_page(self, reference_page: str, page_to_compare: str) -> AnalysisDetails:
        """
        Returns true if 'reference_page' and 'page_to_compare' seem to be the same page
        :param reference_page:  the image file showing the reference page to compare to
        :param page_to_compare: the image file showing the page of the current test
        """
        same_page = True

        if not os.path.isfile(reference_page):
            return AnalysisDetails(same_page, f"Reference file {reference_page} does not exist")
        if not os.path.isfile(page_to_compare):
            return AnalysisDetails(same_page, f"Page to compare file {page_to_compare} does not exist")

        chat_json_response = self.llm_connector.chat_and_expect_json_response(settings.OPEN_WEBUI_PROMPT_WEBPAGE_COMPARISON, [reference_page, page_to_compare], 50)

        if chat_json_response.error:
            return AnalysisDetails(same_page, chat_json_response.error)
        try:
            similarity = int(chat_json_response.response["similarity"])
            return AnalysisDetails(similarity > 70, None)
        except Exception:
            return AnalysisDetails(same_page, "no 'similarity' key present in JSON or value is not a number")

    def is_error_message_displayed(self) -> AnalysisDetails:
        """
        Check whether an error message is displayed in the page
        :return: the error messages or None if no error message has been detected
                    whether there was error in analysis, or None if analysis was successful
        """

        last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name='Test end')
        if len(last_step) > 0:
            last_step = last_step[0]

            try:
                # load details
                step_result_details = json.loads(last_step.stacktrace)
                for snapshot in step_result_details['snapshots']:
                    if snapshot['idImage']:
                        image_file = File.objects.get(pk=snapshot['idImage'])
                        return self.is_error_message_displayed(image_file.file.path)

            except Exception as e:
                return AnalysisDetails([], f"Error reading file for analysis: {str(e)}")

        return AnalysisDetails([], None)

    def is_error_message_displayed(self, image_path: str) -> AnalysisDetails:
        """

        :param image_path:
        :return:
        """
        error_messages = []

        if not os.path.isfile(image_path):
            logger.error(f"File {image_path} does not exist")
            return AnalysisDetails(error_messages, f"File {image_path} does not exist")
        else:
            chat_json_response = self.llm_connector.chat_and_expect_json_response(settings.OPEN_WEBUI_PROMPT_FIND_ERROR_MESSAGE, [image_path])

            if chat_json_response.error:
                return AnalysisDetails(error_messages, chat_json_response.error)
            try:
                if not isinstance(chat_json_response.response["error_messages"], list):
                    error_messages = [str(chat_json_response.response["error_messages"])]
                else:
                    error_messages = chat_json_response.response["error_messages"]
                return AnalysisDetails(error_messages, None)
            except Exception:
                return AnalysisDetails(error_messages, "no 'error_messages' key present in JSON")

    def is_element_present_on_page(self):
        """
        If test fails because an element has not been found, then we want to know if the element is present or not
        It may still be present, but with a different locator
        :return:
        """
        return False

    def has_network_errors(self):
        """
        Check in HAR file of the current test if some error occurred in the current page or the previous one
        :return:
        """
        return False

    def has_network_slowness(self):
        """
        Check in HAR file of the current test if some slowness occurred in the current page or the previous one
        :return:
        """
        return False

    def has_javascript_errors(self):
        """
        Returns the list of javascript errors or empty list if none are seen
        :return:
        """
        return []
