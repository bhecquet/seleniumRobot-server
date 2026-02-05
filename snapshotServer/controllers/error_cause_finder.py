import json
import logging
import os
from collections import namedtuple
from datetime import datetime
from typing import Optional

from django.conf import settings

from snapshotServer.controllers.llm_connector import LlmConnector
from snapshotServer.models import TestCaseInSession, StepResult, File, StepReference, TestStep

ErrorCause = namedtuple("ErrorCause", [
                                        'cause',        # the probable cause of the error (application, scripting, tool, environment
                                       'why',           # what guided us to the probable cause (error message, JS errors, missing field, ...)
                                       'information',    # additional information related to "why"
                                        'analysis_errors' # list of error messages during analysis
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

    def detect_cause(self) -> Optional[ErrorCause]:
        """
        Look for various causes
        """
        if self.test_case_in_session.isOkWithResult():
            return None

        analysis_errors = []

        on_right_page_analysis_details = self.is_on_the_right_page()
        if on_right_page_analysis_details.analysis_error:
            analysis_errors.append("On same page: " + on_right_page_analysis_details.analysis_error)

        # in case analysis cannot be done, we assume we are on the right page
        if on_right_page_analysis_details.details:

            if self.is_element_present_on_page():
                # TODO: send the DOM and the image to the LLM
                return ErrorCause("script", "bad_locator", None, analysis_errors)
            else:
                return self.detect_other_causes(analysis_errors)

        else:
            # check for error messages
            error_messages_analysis_details = self.is_error_message_displayed_in_last_step()
            if error_messages_analysis_details.analysis_error:
                analysis_errors.append("Error message: " + error_messages_analysis_details.analysis_error)

            if error_messages_analysis_details.details:
                return ErrorCause("application_error", "error_message", error_messages_analysis_details.details, analysis_errors)

            # check if we are on previous page
            on_previous_page_analysis_details = self.is_on_the_previous_page()
            if on_previous_page_analysis_details.analysis_error:
                analysis_errors.append("On previous page: " + on_previous_page_analysis_details.analysis_error)

            elif on_previous_page_analysis_details.details:
                return self.detect_other_causes(analysis_errors)
            else:
                return ErrorCause("application_change", "right_page", None, analysis_errors)

    def detect_other_causes(self, analysis_errors: list) -> ErrorCause:
        js_errors_analysis_details = self.has_javascript_errors()
        if js_errors_analysis_details.analysis_error:
            analysis_errors.append("JS error: " + js_errors_analysis_details.analysis_error)


        if js_errors_analysis_details.details:
            return ErrorCause("application_error", "javascript_error", js_errors_analysis_details.details, analysis_errors)
        elif self.has_network_errors():
            return ErrorCause("application_error", "network_error", "Consult HAR file", analysis_errors)
        elif self.has_network_slowness():
            return ErrorCause("environment", "network_slowness", "Consult HAR file", analysis_errors)
        else:
            return ErrorCause("script", "unknown", None, analysis_errors)

    def is_on_the_right_page(self) -> AnalysisDetails:
        """
        Check whether test was on the right page when error occurred
        If no failed step can be found, skip
        :return: [true/false, <analysis error if any>] if test is on the right page
        """
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
        if len(failed_step_result) > 0:
            return self.is_step_on_same_page(failed_step_result[0], failed_step_result[0])

        return AnalysisDetails(True, "No image to compare")


    def is_on_the_previous_page(self) -> AnalysisDetails:
        """
        If we are not on the right page, we may be on the previous page which means that a previous click did not produce the expected action
        :return:
        """
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
        if len(failed_step_result) > 0:

            previous_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, pk__lt=failed_step_result[0].id).order_by('-pk')
            if len(previous_step_result) > 0:
                return self.is_step_on_same_page(previous_step_result[0], failed_step_result[0])
            else:
                return AnalysisDetails(True, "No image to compare from previous step")

        return AnalysisDetails(True, "No image to compare")

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

        if len(step_reference) == 0 or not step_reference[0].image or not os.path.isfile(step_reference[0].image.path):
            return AnalysisDetails(True, f"No reference image for step '{failed_step_result.step.name}' in test case '{self.test_case_in_session.testCase.name}'")

        try:
            # load details
            step_result_details = json.loads(failed_step_result.stacktrace)
            for snapshot in step_result_details['snapshots']:
                if snapshot['idImage'] and snapshot['snapshotCheckType'] == 'NONE_REFERENCE':
                    image_file = File.objects.get(pk=snapshot['idImage'])
                    return self.is_on_same_page(step_reference[0].image.path, image_file.file.path)

            return AnalysisDetails(True, f"No image available for the failed step: {failed_step_result.step.name}")

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

    def is_error_message_displayed_in_last_step(self) -> AnalysisDetails:
        """
        Check whether an error message is displayed in the page
        :return: the error messages or empty list if no error message has been detected
                    whether there was error in analysis, or None if analysis was successful
        """

        last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name=TestStep.LAST_STEP_NAME)
        if len(last_step) > 0:
            last_step = last_step[0]

            try:
                # load details
                step_result_details = json.loads(last_step.stacktrace)
                error_messages = []
                analysis_errors = []

                if not step_result_details['snapshots']:
                    return AnalysisDetails(error_messages, "No snapshot to analyze")

                for snapshot in step_result_details['snapshots']:
                    if snapshot['idImage']:
                        image_file = File.objects.get(pk=snapshot['idImage'])
                        analysis_details = self.is_error_message_displayed(image_file.file.path)
                        error_messages += analysis_details.details
                        if analysis_details.analysis_error:
                            analysis_errors.append(analysis_details.analysis_error)

                return AnalysisDetails(error_messages, '\n'.join(analysis_errors) if analysis_errors else None)

            except Exception as e:
                return AnalysisDetails([], f"Error reading file for analysis: {str(e)}")

        return AnalysisDetails([], f"No '{TestStep.LAST_STEP_NAME}' step to analyze")

    def is_error_message_displayed(self, image_path: str) -> AnalysisDetails:
        """

        :param image_path:
        :return: AnalysisDetails where 'details' contains list of error messages
        """
        error_messages = []

        if not os.path.isfile(image_path):
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

    def has_javascript_errors(self) -> AnalysisDetails:
        """
        Returns the list of javascript errors or empty list if none are seen
        Browser logs are recorded to 'Test end' step
        """
        last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name=TestStep.LAST_STEP_NAME)
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')

        if len(last_step) > 0 and len(failed_step_result) > 0:
            last_step = last_step[0]
            failed_step_result = failed_step_result[0]

            try:
                # load details
                last_step_result_details = json.loads(last_step.stacktrace)
                failed_step_result_details = json.loads(failed_step_result.stacktrace)
                for file_info in last_step_result_details['files']:
                    if file_info["name"] == "Browser log file":
                        log_file = File.objects.get(pk=file_info['id'])
                        return self._analyze_javascript_logs(log_file.file.path, failed_step_result_details['timestamp'])

                return AnalysisDetails([], "No browser logs to analyze")
            except Exception as e:
                return AnalysisDetails([], f"Error reading step details for analysis: {str(e)}")

        return AnalysisDetails([], f"No '{TestStep.LAST_STEP_NAME}' step where logs can be found")

    def _analyze_javascript_logs(self, log_file_path: str, failed_step_result_timestamp: int) -> AnalysisDetails:
        """
        Analyze log file, looking for logs that happen after the start of the failed step
        Filtering is done only on "SEVERE" messages
        :param log_file_path:                   path to browser log file
        :param failed_step_result_timestamp:    timestamp in milliseconds
        :return:
        """
        if 'chrome' in self.test_case_in_session.session.browser.lower() or 'edge' in self.test_case_in_session.session.browser.lower():
            logs = []
            try:
                with open(log_file_path, 'r') as log_file:
                    for line in log_file:
                        log_timestamp = datetime.strptime(line.split("]")[0][1:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp() * 1000 # in milliseconds
                        if log_timestamp > failed_step_result_timestamp and "severe" in line.lower():
                            logs.append(line.strip())

                    return AnalysisDetails(logs, None)

            except Exception as e:
                return AnalysisDetails([], "Error reading log file: " + str(e))


        else:
            return AnalysisDetails([], "Only chrome / Edge logs can be analyzed")
