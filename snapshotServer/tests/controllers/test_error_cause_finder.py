import os
import json
from typing import Optional
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.conf import settings

from snapshotServer.controllers.error_cause_finder import ErrorCauseFinder

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

class TestErrorCauseFinder(TestCase):

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

    def test_analyze_image_with_error_message(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ErrorCauseFinder(None)
        error_displayed, error_messages, analysis_error = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/image_with_error_message_small1.png')
        self.assertTrue(error_displayed)
        self.assertEquals('Nom d’utilisateur ou mot de passe incorrect', error_messages[0])
        self.assertIsNone(analysis_error)


    def test_compare_image_with_an_other_similar_image(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ErrorCauseFinder(None)
        same_page, analysis_error = error_cause_finder._is_on_same_page('snapshotServer/tests/data/image_with_error_message1.png', 'snapshotServer/tests/data/image_without_error_message.png')
        self.assertTrue(same_page)
        self.assertIsNone(analysis_error)

    def test_compare_image_with_an_other_different_image(self):
        """
        Test to be executed with a real OpenWebUI instance
        """
        error_cause_finder = ErrorCauseFinder(None)
        same_page, analysis_error = error_cause_finder._is_on_same_page('snapshotServer/tests/data/image_with_error_message1.png', 'snapshotServer/tests/data/Ibis_Mulhouse.png')
        self.assertFalse(same_page)
        self.assertIsNone(analysis_error)

    def _analyze_image(self, reply: object, expected_error_message: list, expected_analysis_error: Optional[str]):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ErrorCauseFinder(None)
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            analysis_details = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/image_with_error_message_small1.png')
            self.assertEqual(expected_error_message, analysis_details.details)
            self.assertEqual(expected_analysis_error, analysis_details.analysis_error)

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_error_message_mocked(self):
        """
        Test standard case where error message is discovered
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")],
                            ["Bad user name"],
                            None)

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_openwebui_error_mocked(self):
        """
        Test when HTTP error is returned
        """
        self._analyze_image([Response(500, "KO")],
                            [],
                            "No response from Open WebUI:Error chating with Open WebUI: KO")


    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_mocked(self):
        """
        Test standard case where error message is not discovered
        :return:
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n\\n  ]\\n}\\n```")],
                    [],
                    None)

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_error_message_invalid_json_mocked(self):
        """
        Invalid JSON returned by LLM
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": \\n}\\n```")],
                            [],
                            "Invalid JSON returned by model")

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_missing_required_field_mocked(self):
        """
        'error_messages field is not present is reply'
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_message\\\": [\\n\\n  ]\\n}\\n```")],
                            [],
                            "no 'error_messages' key present in JSON")

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_error_messages_no_list_mocked(self):
        """
        'error_messages' field returns a string, not a list
        """
        self._analyze_image([Response(200, self.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": \\\"an error message\\\"\\n}\\n```")],
                            ["an error message"],
                            None)

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_without_error_message_openwebui_error_mocked(self):
        """
        Check that if error occurs during LLM query, this error is returned in analysis_error
        """
        self._analyze_image([Exception('OpenWebUI error')],
                            [],
                             "No response from Open WebUI:Error chating with Open WebUI: OpenWebUI error")


    def _analyze_images(self, reply: object, expected_is_on_same_page: bool, expected_analysis_error: Optional[str]):
        with patch('requests.post') as mock_request:
            mock_request.side_effect = reply
            error_cause_finder = ErrorCauseFinder(None)
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
        error_cause_finder = ErrorCauseFinder(None)
        error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
        analysis_details = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_not_present.png', 'snapshotServer/tests/data/image_with_error_message_small1.png')
        self.assertEqual(True, analysis_details.details)
        self.assertEqual("Reference file snapshotServer/tests/data/image_not_present.png does not exist", analysis_details.analysis_error)

    @override_settings(OPEN_WEBUI_URL='')
    def test_is_on_same_page_wrong_file2_mocked(self):
        """
        If reference file is not present, return error
        """
        error_cause_finder = ErrorCauseFinder(None)
        error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
        analysis_details = error_cause_finder.is_on_same_page('snapshotServer/tests/data/image_with_error_message_small1.png', 'snapshotServer/tests/data/image_not_present.png')
        self.assertEqual(True, analysis_details.details)
        self.assertEqual("Page to compare file snapshotServer/tests/data/image_not_present.png does not exist", analysis_details.analysis_error)
