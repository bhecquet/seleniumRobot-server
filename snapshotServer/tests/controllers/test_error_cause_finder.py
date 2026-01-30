import os
import json
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

    @override_settings(OPEN_WEBUI_URL='')
    def test_analyze_image_with_error_message_mocked(self):

        with patch('requests.post') as mock_request:
            mock_request.side_effect = [Response(200, "{}")]
            error_cause_finder = ErrorCauseFinder(None)
            error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()
            error_displayed, error_messages, analysis_error = error_cause_finder.is_error_message_displayed('snapshotServer/tests/data/image_with_error_message_small1.png')
