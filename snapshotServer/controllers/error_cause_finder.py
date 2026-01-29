import base64
import json
import logging
import os
import time
from collections import namedtuple

import requests
from openwebui_chat_client import OpenWebUIClient

from django.conf import settings

from snapshotServer.models import TestCaseInSession, StepResult, File

ErrorCause = namedtuple("ErrorCause", [
                                        'cause',        # the probable cause of the error (application, scripting, tool, environment
                                       'why',           # what guided us to the probable cause (error message, JS errors, missing field, ...)
                                       'information'    # additional information related to "why"
])

logger = logging.getLogger(__name__)

class ErrorCauseFinder:
    """
    Class that tries to find what went wrong during the test
    """

    def __init__(self, test_case_in_session: TestCaseInSession):

        self.test_case_in_session = test_case_in_session
        self.open_web_ui_client = None
        if settings.OPEN_WEBUI_URL and settings.OPEN_WEBUI_TOKEN and settings.OPEN_WEBUI_MODEL:
            self.open_web_ui_client = OpenWebUIClient(
                base_url=settings.OPEN_WEBUI_URL,
                token=settings.OPEN_WEBUI_TOKEN,
                default_model_id=settings.OPEN_WEBUI_MODEL
            )


    def detect_cause(self):
        """
        Look for various causes
        """
        if self.test_case_in_session.isOkWithResult():
            return None

        if self.is_on_the_right_page():
            if self.is_element_present_on_page():
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
            error_message = self.is_error_message_displayed()
            if error_message:
                return ErrorCause("application_error", "error_message", error_message)
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
        :return: true if test is on the right page
        """
        return True

    def is_on_the_previous_page(self):
        """
        If we are not on the right page, we may be on the previous page which means that a previous click did not produce the expected action
        :return:
        """
        return False

    def is_error_message_displayed(self):
        """
        Check whether an error message is displayed in the page
        :return: the error messages or None if no error message has been detected
                    whether there was error in analysis, or None if analysis was successful
        """
        if self.open_web_ui_client and len(self.open_web_ui_client.list_models()) > 0:

            last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name='Test end')
            if len(last_step) > 0:
                last_step = last_step[0]

                try:
                    # load details
                    step_result_details = json.loads(last_step.stacktrace)
                    for snapshot in step_result_details['snapshots']:
                        if snapshot['idImage']:
                            image_file = File.objects.get(pk=snapshot['idImage'])
                            error_displayed, error_messages, analysis_error = self.is_error_message_displayed(image_file.file.path)

                            if error_displayed:
                                return error_messages, None
                            elif analysis_error:
                                return [], analysis_error
                            else:
                                return [], None

                except Exception as e:
                    return [], f"Error reading file for analysis: {str(e)}"

        return [], None

    def is_error_message_displayed(self, image_path):
        error_messages = []
        error_displayed = False
        chat_title = "Error Analysis"

        if not os.path.isfile(image_path):
            logger.error(f"File {image_path} does not exist")
            return error_displayed, error_messages, f"File {image_path} does not exist"
        else:
            result = self._call_open_web_ui_with_file(settings.OPEN_WEBUI_PROMPT_FIND_ERROR_MESSAGE, image_path)
            # result = self.open_web_ui_client.chat(question=settings.OPEN_WEBUI_PROMPT_FIND_ERROR_MESSAGE,
            #                                           chat_title=chat_title,
            #                                           image_paths=[image_path])
            if 'choices' in result and len(result['choices']) > 0:
                logger.info("LLM response in %.2f secs" % (result['usage']['total_duration'] / 1000000000.,))
                response_str = result['choices'][0]['message']['content'].replace('```json', '').replace('```', '')
                try:
                    response = json.loads(response_str.replace('\n', ''))
                except:
                    return error_displayed, error_messages, "Invalid JSON returned by model"
                try:
                    error_messages = response["error_messages"]
                    return len(error_messages) > 0, error_messages, None
                except:
                    return error_displayed, error_messages, "no 'error_messages' key present in JSON"
            else:
                logger.error("No response from Open WebUI")
                return error_displayed, error_messages, "No response from Open WebUI"



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

    def _call_open_web_ui_with_file(self, prompt, file_path):
        headers = {
            'Authorization': f'Bearer {settings.OPEN_WEBUI_TOKEN}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": settings.OPEN_WEBUI_MODEL,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            }

        if file_path and os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                data['messages'][0]['content'].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64," + base64.b64encode(file.read()).decode("utf-8")
                    }
                })
        response = requests.post(settings.OPEN_WEBUI_URL + '/api/chat/completions', headers=headers, json=data)
        return response.json()