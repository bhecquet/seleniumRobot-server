import json
import os
from typing import Optional
from unittest.mock import patch
from django.test import TestCase, override_settings

from snapshotServer.controllers.error_cause.image_error_cause_finder import ImageErrorCauseFinder
from snapshotServer.controllers.llm_connector import ChatJsonResponse
from snapshotServer.models import StepResult, TestCaseInSession, TestCase as SnapshotServerTestCase, StepReference, \
    Error


class Response:

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        self.text = content

    def json(self):
        return json.loads(self.content)

class MockedOpenWebUiClient:

    def list_models(self):
        return ['foo']

class TestImageErrorCauseFinder(TestCase):

    openwebui_message_template = '''{
      "id": "ministral-3:8b-c8fc938a-f3cf-4c2f-8f86-1f33ca30e0d2",
      "created": 1769704953,
      "model": "ministral-3:8b",
      "choices": [
        {
          "index": 0,
          "logprobs": null,
          "finish_reason": "stop",
          "message": {
            "role": "assistant",
            "content": "%s"
          }
        }
      ],
      "object": "chat.completion",
      "usage": {
        "response_token/s": 38.0,
        "prompt_token/s": 226.26,
        "total_duration": 18652655041,
        "load_duration": 2433031541,
        "prompt_eval_count": 2345,
        "prompt_tokens": 2345,
        "prompt_eval_duration": 10364220042,
        "eval_count": 217,
        "completion_tokens": 217,
        "eval_duration": 5709893745,
        "approximate_total": "0h0m18s",
        "total_tokens": 2562,
        "completion_tokens_details": {
          "reasoning_tokens": 0,
          "accepted_prediction_tokens": 0,
          "rejected_prediction_tokens": 0
        }
      }
    }'''
    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']
    
    def test_analyze_image_with_error_message(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        error_displayed, error_messages, analysis_error = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/image_with_error_message_small1.png')
        self.assertTrue(error_displayed)
        self.assertEquals('Nom d’utilisateur ou mot de passe incorrect', error_messages[0])
        self.assertIsNone(analysis_error)
    
    
    def test_compare_image_with_an_other_similar_image(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        same_page, analysis_error = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_with_error_message1.png', 'snapshotServer/tests/data/image_without_error_message.png')
        self.assertTrue(same_page)
        self.assertIsNone(analysis_error)
    
    def test_compare_image_with_an_other_different_image(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        element_present, analysis_error = error_cause_finder.is_element_present('snapshotServer/tests/data/order_page.jpg', "radio button with label 'destinataire'")
        self.assertTrue(element_present)
        self.assertIsNone(analysis_error)

    def test_check_element_present_on_page(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        same_page, analysis_error = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_with_error_message1.png', 'snapshotServer/tests/data/Ibis_Mulhouse.png')
        self.assertFalse(same_page)
        self.assertIsNone(analysis_error)
    
    def _analyze_image(self, reply: object, expected_error_message: list, expected_analysis_error: Optional[str], open_webui_called: bool):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ImageErrorCauseFinder(None)
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/image_with_error_message_small1.png')
            self.assertEqual(expected_error_message, analysis_details.details)
            self.assertEqual(expected_analysis_error, analysis_details.analysis_error)
    
            if open_webui_called:
                args = mock_request.call_args
                self.assertEqual(('/api/chat/completions',), args[0])
                self.assertEqual({'Authorization': 'Bearer abc', 'Content-Type': 'application/json'}, args[1]['headers'])
                self.assertTrue(args[1]['json']['messages'][0]['content'][1]['image_url']['url'].startswith("data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAABJMAAAJ+CAYAAAAHeUHiAAEAAElEQVR4nOz9S7IkSZItiB0W9/hlZlVXPXqvCdQLwQCLwBIwA2GMlWE3WAaIMGh0Voa7MgbC5yN6b2QVGrNw4UyPa6amKsLCwiJm5ygza/2f/x//zy")) # check right file is used
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_error_message_mocked(self):
        """
        Test standard case where error message is discovered
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                            ["Bad user name"],
                            None,
                            True)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_openwebui_error_mocked(self):
        """
        Test when HTTP error is returned
        """
        self._analyze_image([Response(500, "KO")],
                            [],
                            "No response from Open WebUI:Error chating with Open WebUI: KO",
                            True)
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_mocked(self):
        """
        Test standard case where error message is not discovered
        :return:
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n\\n  ]\\n}\\n```")],
                            [],
                            None,
                            True)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_invalid_file_mocked(self):
        """
        Test that we check if file exists
        """
        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")]
            error_cause_finder = ImageErrorCauseFinder(None)
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/invalid_file.png')
            self.assertEqual([], analysis_details.details)
            self.assertEqual("File snapshotServer/tests/data/invalid_file.png does not exist", analysis_details.analysis_error)
    
            mock_request.assert_not_called()
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_error_message_invalid_json_mocked(self):
        """
        Invalid JSON returned by LLM
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": \\n}\\n```")],
                            [],
                            "Invalid JSON returned by model",
                            True)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_missing_required_field_mocked(self):
        """
        'error_messages field is not present is reply'
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_message\\\": [\\n\\n  ]\\n}\\n```")],
                            [],
                            "no 'error_messages' key present in JSON",
                            True)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_error_messages_no_list_mocked(self):
        """
        'error_messages' field returns a string, not a list
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": \\\"an error message\\\"\\n}\\n```")],
                            ["an error message"],
                            None,
                            True)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_openwebui_error_mocked(self):
        """
        Check that if error occurs during LLM query, this error is returned in analysis_error
        """
        self._analyze_image([Exception('OpenWebUI error')],
                            [],
                            "No response from Open WebUI:Error chating with Open WebUI: OpenWebUI error",
                            True)
    
    def _is_error_message_displayed(self, reply: object, expected_error_messages: list, expected_analysis_error: Optional[str]):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed_in_last_step()
            self.assertEqual(expected_error_messages, analysis_details.details)
            self.assertEqual(expected_analysis_error, analysis_details.analysis_error)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_mocked(self):
        self._is_error_message_displayed([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                                         ["Bad user name"],
                                         None
                                         )
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_no_test_end_step_mocked(self):
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.testCase = TestCaseInSession.objects.get(pk=1)
        test_end_step_result.save()
        self._is_error_message_displayed([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                                         [],
                                         "No 'Test end' step to analyze"
                                         )
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_wrongly_formatted_json_mocked(self):
        """
        test when json is incorrect
        :return:
        """
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = ""
        test_end_step_result.save()
        self._is_error_message_displayed([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                                         [],
                                         "Error reading file for analysis: Expecting value: line 1 column 1 (char 0)"
                                         )
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_wrongly_formatted_json2_mocked(self):
        """
        snapshot key is missing in json
        """
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = """{
                    "exception": "class java.lang.AssertionError",
                    "date": "Wed Oct 25 18:06:14 CEST 2023",
                    "failed": true,
                    "type": "step",
                    "duration": 277,
                    "videoTimeStamp": 10519,
                    "name": "Test end",
                    "files": [
                        {
                            "name": "Video capture",
                            "id": 112,
                            "type": "file"
                        }
                    ],
                    "position": 3,
                    "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
                    "timestamp": 1698257174038,
                    "status": "FAILED",
                    "harCaptures": [
                        {
                            "name": "main",
                            "id": 113,
                            "type": "networkCapture"
                        }
                    ]
                }"""
        test_end_step_result.save()
        self._is_error_message_displayed([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                                         [],
                                         "Error reading file for analysis: 'snapshots'"
                                         )
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_no_snapshot_mocked(self):
        """
        no snapshot present
        """
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = """{
                    "exception": "class java.lang.AssertionError",
                    "date": "Wed Oct 25 18:06:14 CEST 2023",
                    "failed": true,
                    "type": "step",
                    "duration": 277,
                    "snapshots": [],
                    "videoTimeStamp": 10519,
                    "name": "Test end",
                    "files": [
                        {
                            "name": "Video capture",
                            "id": 112,
                            "type": "file"
                        }
                    ],
                    "position": 3,
                    "actions": [],
                    "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
                    "timestamp": 1698257174038,
                    "status": "FAILED",
                    "harCaptures": [
                        {
                            "name": "main",
                            "id": 113,
                            "type": "networkCapture"
                        }
                    ]
                }"""
        test_end_step_result.save()
        self._is_error_message_displayed([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                                         [],
                                         "No snapshot to analyze"
                                         )
    
    stacktrace_with_multiple_files = """{
                    "exception": "class java.lang.AssertionError",
                    "date": "Wed Oct 25 18:06:14 CEST 2023",
                    "failed": true,
                    "type": "step",
                    "duration": 277,
                    "snapshots": [
                        {
                            "idHtml": 110,
                            "displayInReport": true,
                            "name": "drv:main",
                            "idImage": 108,
                            "failed": false,
                            "position": 0,
                            "type": "snapshot",
                            "title": "Current Window: S'identifier [Jenkins]",
                            "snapshotCheckType": "NONE",
                            "url": "https://jenkins/jenkins/loginError",
                            "timestamp": 1698257174417
                        },
                        {
                            "idHtml": 110,
                            "displayInReport": true,
                            "name": "drv:main",
                            "idImage": 111,
                            "failed": false,
                            "position": 0,
                            "type": "snapshot",
                            "title": "An other window",
                            "snapshotCheckType": "NONE",
                            "url": "https://jenkins/jenkins/login",
                            "timestamp": 1698257174418
                        }
                    ],
                    "videoTimeStamp": 10519,
                    "name": "Test end",
                    "files": [
                        {
                            "name": "Video capture",
                            "id": 112,
                            "type": "file"
                        }
                    ],
                    "position": 3,
                    "actions": [],
                    "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
                    "timestamp": 1698257174038,
                    "status": "FAILED",
                    "harCaptures": [
                        {
                            "name": "main",
                            "id": 113,
                            "type": "networkCapture"
                        }
                    ]
                }
            """

    stacktrace_no_file = """{
                    "exception": "class java.lang.AssertionError",
                    "date": "Wed Oct 25 18:06:14 CEST 2023",
                    "failed": true,
                    "type": "step",
                    "duration": 277,
                    "snapshots": [
                        {
                            "displayInReport": true,
                            "name": "drv:main",
                            "failed": false,
                            "position": 0,
                            "type": "snapshot",
                            "title": "Current Window: S'identifier [Jenkins]",
                            "snapshotCheckType": "NONE",
                            "url": "https://jenkins/jenkins/loginError",
                            "timestamp": 1698257174417
                        }
                    ],
                    "videoTimeStamp": 10519,
                    "name": "Test end",
                    "files": [],
                    "position": 3,
                    "actions": [],
                    "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
                    "timestamp": 1698257174038,
                    "status": "FAILED",
                    "harCaptures": []
                }
            """
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_on_multiple_images_mocked(self):
        """
        Check that when last step contains several images, all of them are analyzed
        """
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_with_multiple_files
        test_end_step_result.save()
    
        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```"),
                                        Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Technical error\\\"\\n  ]\\n}\\n```")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed_in_last_step()
            self.assertEqual(["Bad user name", "Technical error"], analysis_details.details)
            self.assertIsNone(analysis_details.analysis_error)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_no_image_file_mocked(self):
        """
        Check that when last step contains several images, all of them are analyzed
        """
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_no_file
        test_end_step_result.save()

        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(500, "")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed_in_last_step()
            self.assertEqual([], analysis_details.details)
            self.assertEqual("No image provided", analysis_details.analysis_error)


    @override_settings(OPEN_WEBUI_URL='')
    def test_is_error_message_displayed_on_multiple_images2_mocked(self):
        """
        Check that if any error occurs during analysis of one image, no information is lost
        """
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_with_multiple_files
        test_end_step_result.save()
    
        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```"),
                                        Response(500, "KO")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed_in_last_step()
            self.assertEqual(["Bad user name"], analysis_details.details)
            self.assertEqual("No response from Open WebUI:Error chating with Open WebUI: KO", analysis_details.analysis_error)
    
    
    def _analyze_images(self, reply: object, expected_is_on_same_page: bool, expected_analysis_error: Optional[str]):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ImageErrorCauseFinder(None)
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_with_error_message_small1.png', 'snapshotServer/tests/data/image_with_error_message_small1.png')
            self.assertEqual(expected_is_on_same_page, analysis_details.details)
            self.assertEqual(expected_analysis_error, analysis_details.analysis_error)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_mocked(self):
        """
        Check both images represent the same page
        """
        self._analyze_images([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                             True,
                             None)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_not_on_same_page_mocked(self):
        """
        Check both images do not represent the same page (similarity < 70%)
        """
        self._analyze_images([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 70\\n}\\n```")],
                             False,
                             None)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_chat_error_mocked(self):
        """
        Error returned when chatting, check error is propagated
        """
        self._analyze_images([Response(500, "KO")],
                             True,
                             "No response from Open WebUI:Error chating with Open WebUI: KO")
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_wrong_response_format_mocked(self):
        """
        if JSON does not provide the expected key, raise error
        """
        self._analyze_images([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similar\\\": 70\\n}\\n```")],
                             True,
                             "no 'similarity' key present in JSON or value is not a number")
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_wrong_response_format2_mocked(self):
        """
        Similarity is a string, check we try to make it int
        """
        self._analyze_images([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": \\\"70\\\"\\n}\\n```")],
                             False,
                             None)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_invalid_json_mocked(self):
        """
        Similarity is a string, check we try to make it int
        """
        self._analyze_images([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\" \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 70\\n}\\n```")],
                             True,
                             'Invalid JSON returned by model')
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_wrong_file_mocked(self):
        """
        If reference file is not present, return error
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
        analysis_details = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_not_present.png', 'snapshotServer/tests/data/image_with_error_message_small1.png')
        self.assertEqual(True, analysis_details.details)
        self.assertEqual("Reference file snapshotServer/tests/data/image_not_present.png does not exist", analysis_details.analysis_error)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_wrong_file2_mocked(self):
        """
        If reference file is not present, return error
        """
        error_cause_finder = ImageErrorCauseFinder(None)
        error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
        analysis_details = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_with_error_message_small1.png', 'snapshotServer/tests/data/image_not_present.png')
        self.assertEqual(True, analysis_details.details)
        self.assertEqual("Page to compare file snapshotServer/tests/data/image_not_present.png does not exist", analysis_details.analysis_error)
    
    def _is_step_on_same_page(self, reply: object, expected_details: bool, expected_analysis_error: Optional[str]):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_step_on_same_page(
                StepResult.objects.get(pk=3), # StepResult when test was OK
                StepResult.objects.get(pk=13)) # StepResult for the currently failed step
            self.assertEqual(expected_details, analysis_details.details)
            self.assertEqual(expected_analysis_error, analysis_details.analysis_error)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_step_on_same_page_mocked(self):
        self._is_step_on_same_page([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                                   True,
                                   None)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_step_on_same_page_no_step_reference_found_mocked(self):
        # update TCIS so that no step reference can be found
        tcis = TestCaseInSession.objects.get(pk=11)
        tcis.testCase = SnapshotServerTestCase.objects.get(pk=2)
        tcis.save()
        self._is_step_on_same_page([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                                   True,
                                   "No reference image for step 'getErrorMessage' in test case 'loginInvalid'")
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_step_on_same_page_no_image_for_step_reference_mocked(self):
        # update TCIS so that no step reference can be found
        step_reference = StepReference.objects.get(pk=3)
        step_reference.image = None
        step_reference.save()
        self._is_step_on_same_page([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                                   True,
                                   "No reference image for step 'getErrorMessage' in test case 'loginInvalid'")
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_step_on_same_page_no_image_in_failed_step_mocked(self):
        """
        if failed step does not have associated 'step_start_state' image, do not try to compare
        :return:
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.stacktrace = '''{
            "date": "Wed Oct 25 18:06:07 CEST 2023",
            "failed": true,
            "type": "step",
            "duration": 5539,
            "snapshots": [
                {
                    "idHtml": null,
                    "displayInReport": true,
                    "name": "Valid-reference",
                    "idImage": 109,
                    "failed": false,
                    "position": 2,
                    "type": "snapshot",
                    "snapshotCheckType": "NONE",
                    "timestamp": 1698257180743
                }
            ],
            "videoTimeStamp": 4350,
            "name": "getErrorMessage<> ",
            "files": [],
            "position": 2,
            "actions": [
            ],
            "timestamp": 1698257167869,
            "status": "FAILED",
            "harCaptures": []
        }'''
        failed_step_result.save()
        self._is_step_on_same_page([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                                   True,
                                   "No image available for the failed step: getErrorMessage")
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_step_on_same_page_wrong_formatted_details_mocked(self):
        """
        If step details are not correctly formatted, or are missing required 'snapshots', signal error
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.stacktrace = '''{
            "date": "Wed Oct 25 18:06:07 CEST 2023",
            "failed": true,
            "type": "step",
            "duration": 5539,
            "videoTimeStamp": 4350,
            "name": "getErrorMessage<> ",
            "files": [],
            "position": 2,
            "actions": [
            ],
            "timestamp": 1698257167869,
            "status": "FAILED",
            "harCaptures": []
        }'''
        failed_step_result.save()
        self._is_step_on_same_page([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")],
                                   True,
                                   "Error reading file for analysis: 'snapshots'")

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_the_right_page_mocked(self):
    
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            mock_llm_connector.chat_and_expect_json_response.side_effect = [ChatJsonResponse({"explanation": "foo", "similarity": 71}, None)]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_on_the_right_page()
            self.assertTrue(analysis_details.details)
            self.assertIsNone(analysis_details.analysis_error)
            used_files = mock_llm_connector.chat_and_expect_json_response.call_args[0][1]
            self.assertEqual('test_Image3.png', os.path.basename(used_files[0])) # reference for step 3
            self.assertEqual('test_Image1Mod.png', os.path.basename(used_files[1])) # image for step 3 of failed test (it's the failed step)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_the_right_page_without_failed_step_mocked(self):
        """
        If no regular step (not the 'Test end' step), it's not possible to know where to analyze
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result=True
        failed_step_result.save()
    
        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"similarity\\\": 71\\n}\\n```")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_on_the_right_page()
            self.assertTrue(analysis_details.details)
            self.assertEqual("No image to compare", analysis_details.analysis_error)
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_the_previous_page_mocked(self):
        """
        Check that the files sent to LLM are the expected ones
        - one file from the failed step
        - to compare with the reference image of the previous step
        """
    
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            mock_llm_connector.chat_and_expect_json_response.side_effect = [ChatJsonResponse({"explanation": "foo", "similarity": 71}, None)]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_on_the_previous_page()
            self.assertTrue(analysis_details.details)
            self.assertIsNone(analysis_details.analysis_error)
            used_files = mock_llm_connector.chat_and_expect_json_response.call_args[0][1]
            self.assertEqual('test_Image2.png', os.path.basename(used_files[0])) # reference for step 2
            self.assertEqual('test_Image1Mod.png', os.path.basename(used_files[1])) # image for step 3 of failed test (it's the failed step)
    
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_the_previous_page_no_failed_step_found_mocked(self):
        """
        Check that if no failed step is found, error is raised
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result=True
        failed_step_result.save()
    
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_on_the_previous_page()
            self.assertTrue(analysis_details.details)
            self.assertEqual("No image to compare", analysis_details.analysis_error)
    
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_the_previous_page_no_previous_step_found_mocked(self):
        """
        Check that if no previous step is found, we raise an error
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result=True
        failed_step_result.save()
        new_failed_step_result = StepResult.objects.get(pk=11)
        new_failed_step_result.result=False
        new_failed_step_result.save()
    
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_on_the_previous_page()
            self.assertTrue(analysis_details.details)
            self.assertEqual("No image to compare from previous step", analysis_details.analysis_error)

    def _is_element_present(self, reply: object, expected_element_present: bool, expected_analysis_error: Optional[str]):
            with patch('requests.post') as mock_request:
                mock_request.side_effect = reply
                error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
                error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
                analysis_details = error_cause_finder.is_element_present_on_last_step()
                self.assertEqual(expected_element_present, analysis_details.details)
                self.assertEqual(expected_analysis_error, analysis_details.analysis_error)

    def _prepare_error(self, exception: str, element: str):
        error = Error.objects.get(pk=13)
        error.exception = exception
        error.element = element
        error.save()

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_mocked(self):
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```")],
                                         True,
                                         None
                                         )
    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_no_last_step_mocked(self):
        StepResult.objects.get(pk=14).delete()
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```")],
                                         False,
                                         "No 'Test end' step to analyze"
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_in_error_mocked(self):
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\"\\n  \\\"present\\\": true\\n}\\n```")],
                                         False,
                                 'Invalid JSON returned by model'
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_not_present_mocked(self):
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": false\\n}\\n```")],
                                         False,
                                         None
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_no_error_mocked(self):
        Error.objects.get(pk=13).delete()
        self._is_element_present([Response(500, '')],
                                         False,
                                         None
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_other_exception_mocked(self):
        """
        Only NoSuchElementException are valid for this method
        :return:
        """
        self._prepare_error("org.openqa.selenium.TimeoutException", "button with text 'next'")
        self._is_element_present([Response(500, '')],
                                         False,
                                 'org.openqa.selenium.TimeoutException is not NoSuchElementException'
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_other_exception_mocked(self):
        """
        Only NoSuchElementException are valid for this method
        :return:
        """
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "")
        self._is_element_present([Response(500, '')],
                                         False,
                                 "No element provided"
                                         )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_no_snapshot_mocked(self):
        """
        no snapshot present
        """
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = """{
                    "exception": "class java.lang.AssertionError",
                    "date": "Wed Oct 25 18:06:14 CEST 2023",
                    "failed": true,
                    "type": "step",
                    "duration": 277,
                    "snapshots": [],
                    "videoTimeStamp": 10519,
                    "name": "Test end",
                    "files": [
                        {
                            "name": "Video capture",
                            "id": 112,
                            "type": "file"
                        }
                    ],
                    "position": 3,
                    "actions": [],
                    "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
                    "timestamp": 1698257174038,
                    "status": "FAILED",
                    "harCaptures": [
                        {
                            "name": "main",
                            "id": 113,
                            "type": "networkCapture"
                        }
                    ]
                }"""
        test_end_step_result.save()
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```")],
                                 False,
                                 'No snapshot to analyze'
                                 )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_wrong_stacktrace_mocked(self):
        """
        no snapshot present
        """
        # do as if the "Test end" step did not exist
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = ""
        test_end_step_result.save()
        self._is_element_present([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```")],
                                 False,
                                 'Error searching element for analysis: Expecting value: line 1 column 1 (char 0)'
                                 )

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_on_multiple_images_mocked(self):
        """
        Check that when last step contains several images, all of them are analyzed
        """
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_with_multiple_files
        test_end_step_result.save()

        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": false\\n}\\n```"),
                                        Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_element_present_on_last_step()
            self.assertEqual(True, analysis_details.details)
            self.assertIsNone(analysis_details.analysis_error)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_no_image_mocked(self):
        """
        Check that when last step does not contain images, no error is raised
        """
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_no_file
        test_end_step_result.save()

        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(500, "")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_element_present_on_last_step()
            self.assertEqual(False, analysis_details.details)
            self.assertEqual('No image provided', analysis_details.analysis_error)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_on_last_step_on_multiple_images2_mocked(self):
        """
        Check that if any error occurs during analysis of one image, no information is lost
        """
        self._prepare_error("org.openqa.selenium.NoSuchElementException", "button with text 'next'")
        test_end_step_result = StepResult.objects.get(pk=14)
        test_end_step_result.stacktrace = self.stacktrace_with_multiple_files
        test_end_step_result.save()

        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"present\\\": true\\n}\\n```"),
                                        Response(500, "KO")]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_element_present_on_last_step()
            self.assertEqual(True, analysis_details.details)
            self.assertEqual('No response from Open WebUI:Error chating with Open WebUI: KO', analysis_details.analysis_error)


    def _test_is_element_present(self, chat_response: list, expected_present: bool, expected_error: Optional[str]):
       with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
           mock_llm_connector.chat_and_expect_json_response.side_effect = chat_response
           error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
           error_cause_finder.llm_connector = mock_llm_connector
           analysis_details = error_cause_finder.is_element_present('snapshotServer/tests/data/image_with_error_message_small1.png', 'button with text "next"')
           self.assertEqual(expected_present, analysis_details.details)
           self.assertEqual(expected_error, analysis_details.analysis_error)
           used_files = mock_llm_connector.chat_and_expect_json_response.call_args[0][1]
           self.assertEqual('image_with_error_message_small1.png', os.path.basename(used_files[0])) # reference for step 3

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_mocked(self):
        self._test_is_element_present([ChatJsonResponse({"explanation": "foo", "present": False}, None),],
                                      False,
                                      None)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_bad_file_mocked(self):
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            mock_llm_connector.chat_and_expect_json_response.side_effect = [ChatJsonResponse({"explanation": "foo", "present": False}, None),]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_element_present('unknown_file.jpg', 'button with text "next"')
            self.assertEqual(False, analysis_details.details)
            self.assertEqual('File unknown_file.jpg does not exist', analysis_details.analysis_error)
            mock_llm_connector.assert_not_called()

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_no_element_description_mocked(self):
        with patch('snapshotServer.controllers.llm_connector.LlmConnector') as mock_llm_connector:
            mock_llm_connector.chat_and_expect_json_response.side_effect = [ChatJsonResponse({"explanation": "foo", "present": False}, None),]
            error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
            error_cause_finder.llm_connector = mock_llm_connector
            analysis_details = error_cause_finder.is_element_present('snapshotServer/tests/data/image_with_error_message_small1.png', '')
            self.assertEqual(False, analysis_details.details)
            self.assertEqual('No description for element', analysis_details.analysis_error)
            mock_llm_connector.assert_not_called()


    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present2_mocked(self):
        self._test_is_element_present([ChatJsonResponse({"explanation": "foo", "present": 'True'}, None),],
                                      True,
                                      None)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_bad_response_mocked(self):
        self._test_is_element_present([ChatJsonResponse({"explanation": "foo", "there": False}, None),],
                                      False,
                                      "no 'present' key present in JSON")

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_element_present_error_in_llm_mocked(self):
        self._test_is_element_present([ChatJsonResponse({"explanation": "foo", "present": False}, "Some error"),],
                                      False,
                                      "Some error")

