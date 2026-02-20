import json
import os

from snapshotServer.controllers.error_cause import AnalysisDetails
from snapshotServer.controllers.llm_connector import LlmConnector
from snapshotServer.models import TestStep, File, StepResult, StepReference, Error
from django.conf import settings


class ImageErrorCauseFinder:

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session
        self.llm_connector = LlmConnector()
        self.failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
        self.last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name=TestStep.LAST_STEP_NAME)

    def is_on_the_right_page(self) -> AnalysisDetails:
        """
        Check whether test was on the right page when error occurred
        If no failed step can be found, skip
        :return: [true/false, <analysis error if any>] if test is on the right page
        """

        if len(self.failed_step_result) > 0:
            return self.is_step_on_same_page(self.failed_step_result[0], self.failed_step_result[0])

        return AnalysisDetails(True, "No image to compare")


    def is_on_the_previous_page(self) -> AnalysisDetails:
        """
        If we are not on the right page, we may be on the previous page which means that a previous click did not produce the expected action
        :return:
        """
        if len(self.failed_step_result) > 0:

            previous_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, pk__lt=self.failed_step_result[0].id).order_by('-pk')
            if len(previous_step_result) > 0:
                return self.is_step_on_same_page(previous_step_result[0], self.failed_step_result[0])
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

        if len(self.last_step) > 0:
            last_step = self.last_step[0]

            try:
                # load details
                step_result_details = json.loads(last_step.stacktrace)
                error_messages = []
                analysis_errors = []

                if not step_result_details['snapshots']:
                    return AnalysisDetails(error_messages, "No snapshot to analyze")

                for snapshot in step_result_details['snapshots']:
                    if snapshot.get('idImage', 0):
                        image_file = File.objects.get(pk=snapshot['idImage'])
                        analysis_details = self.is_error_message_displayed(image_file.file.path)
                        error_messages += analysis_details.details
                        if analysis_details.analysis_error:
                            analysis_errors.append(analysis_details.analysis_error)
                    else:
                        analysis_errors.append("No image provided")

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

    def is_element_present_on_last_step(self) -> AnalysisDetails:
        """
        If test fails because an element has not been found, then we want to know if the element is present or not
        It may still be present, but with a different locator
        :return:
        """
        element_present = False

        if len(self.last_step) > 0:
            last_step = self.last_step[0]

            errors = Error.objects.filter(stepResult__in=StepResult.objects.filter(testCase=self.test_case_in_session))

            try:
                # load details
                step_result_details = json.loads(last_step.stacktrace)
                analysis_errors = []

                if not step_result_details['snapshots']:
                    return AnalysisDetails(element_present, "No snapshot to analyze")

                for snapshot in step_result_details['snapshots']:
                    if snapshot.get('idImage', 0):
                        image_file = File.objects.get(pk=snapshot['idImage'])
                        for error in errors:
                            if not error.element:
                                analysis_errors.append("No element provided")
                                continue
                            elif 'NoSuchElementException' not in error.exception:
                                analysis_errors.append(f"{error.exception} is not NoSuchElementException")
                                continue

                            analysis_details = self.is_element_present(image_file.file.path, error.element)
                            element_present = element_present or analysis_details.details
                            if analysis_details.analysis_error:
                                analysis_errors.append(analysis_details.analysis_error)
                    else:
                        analysis_errors.append("No image provided")

                return AnalysisDetails(element_present, '\n'.join(analysis_errors) if analysis_errors else None)

            except Exception as e:
                return AnalysisDetails(element_present, f"Error searching element for analysis: {str(e)}")

        return AnalysisDetails(element_present, f"No '{TestStep.LAST_STEP_NAME}' step to analyze")

    def is_element_present(self, image_path: str, element_description: str) -> AnalysisDetails:
        """

        :param image_path:              image to analyse
        :param element_description:     the description of the element to search
        :return: AnalysisDetails where 'details' contains list of error messages
        """
        element_present = False

        if not os.path.isfile(image_path):
            return AnalysisDetails(element_present, f"File {image_path} does not exist")
        elif not element_description:
            return AnalysisDetails(element_present, "No description for element")
        else:
            chat_json_response = self.llm_connector.chat_and_expect_json_response(settings.OPEN_WEBUI_PROMPT_FIND_ELEMENT % element_description, [image_path])

            if chat_json_response.error:
                return AnalysisDetails(element_present, chat_json_response.error)
            try:
                if not isinstance(chat_json_response.response["present"], bool):
                    element_present = bool(chat_json_response.response["present"])
                else:
                    element_present = chat_json_response.response["present"]
                return AnalysisDetails(element_present, None)
            except Exception:
                return AnalysisDetails(element_present, "no 'present' key present in JSON")