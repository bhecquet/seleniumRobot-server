import os

from django.test import TestCase
from django.conf import settings

from snapshotServer.controllers.error_cause_finder import ErrorCauseFinder


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