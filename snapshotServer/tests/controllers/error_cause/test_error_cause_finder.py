
import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from snapshotServer.controllers.error_cause import AnalysisDetails, Cause
from snapshotServer.controllers.error_cause.exception_error_cause_finder import ExceptionErrorCauseFinder, \
    ExceptionAnalysisDetails
from snapshotServer.controllers.error_cause.error_cause_finder import ErrorCauseFinder
from snapshotServer.controllers.error_cause.image_error_cause_finder import ImageErrorCauseFinder
from snapshotServer.controllers.error_cause.js_error_cause_finder import JsErrorCauseFinder
from snapshotServer.controllers.error_cause.network_error_cause_finder import NetworkErrorCauseFinder
from snapshotServer.models import TestCaseInSession


class FakeExceptionErrorCauseFinder(ExceptionErrorCauseFinder):
    def __init__(self): pass
    def analyze_error(self) -> ExceptionAnalysisDetails:
        return ExceptionAnalysisDetails(True, 'step', 'search_element', '', None)
class FakeImageErrorCauseFinder(ImageErrorCauseFinder):
    def __init__(self): pass
    def is_on_the_right_page(self) -> AnalysisDetails:
        return AnalysisDetails(True, None)
    def is_on_the_previous_page(self) -> AnalysisDetails:
        return AnalysisDetails(True, None)
    def is_error_message_displayed_in_last_step(self) -> AnalysisDetails:
        return AnalysisDetails([], None)
    def is_element_present_on_last_step(self) -> AnalysisDetails:
        return AnalysisDetails(False, None)
class FakeJsErrorCauseFinder(JsErrorCauseFinder):
    def __init__(self): pass
    def has_javascript_errors(self) -> AnalysisDetails:
        return AnalysisDetails([], None)
class FakeNetworkErrorCauseFinder(NetworkErrorCauseFinder):
    def __init__(self): pass
    def has_network_errors(self) -> AnalysisDetails:
        return AnalysisDetails([], None)
    def has_network_slowness(self) -> AnalysisDetails:
        return AnalysisDetails([], None)


class TestErrorCauseFinder(TestCase):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def setUp(self):
        self.error_cause_finder = ErrorCauseFinder(TestCaseInSession.objects.get(pk=11), FakeJsErrorCauseFinder(), FakeImageErrorCauseFinder(), FakeExceptionErrorCauseFinder(), FakeNetworkErrorCauseFinder())

    @override_settings(OPEN_WEBUI_URL='')
    def test_detect_cause_with_test_ok(self):
        self.assertIsNone(ErrorCauseFinder(TestCaseInSession.objects.get(pk=1)).detect_cause())

    def test_detect_cause_with_assertion(self):
        with patch('snapshotServer.controllers.error_cause.assertion_error_cause_finder.AssertionErrorCauseFinder') as mock_assertion_error_cause_finder:
            mock_assertion_error_cause_finder.is_assertion_error.side_effect = [AnalysisDetails([True, 'step', 'some assertion'], None)]
            self.error_cause_finder.assertion_error_cause_finder = mock_assertion_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual('step_assertion_error', error_cause.why)
            self.assertEqual('some assertion', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_assertion_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.assertion_error_cause_finder.AssertionErrorCauseFinder') as mock_assertion_error_cause_finder:
            mock_assertion_error_cause_finder.is_assertion_error.side_effect = [AnalysisDetails([True, 'scenario', 'some assertion'], None)]
            self.error_cause_finder.assertion_error_cause_finder = mock_assertion_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual('scenario_assertion_error', error_cause.why)
            self.assertEqual('some assertion', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_error_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.assertion_error_cause_finder.AssertionErrorCauseFinder') as mock_assertion_error_cause_finder:
            mock_assertion_error_cause_finder.is_assertion_error.side_effect = [AnalysisDetails([False, 'scenario', 'some assertion'], None)]
            self.error_cause_finder.assertion_error_cause_finder = mock_assertion_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual('scenario_error', error_cause.why)
            self.assertEqual('some assertion', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_error_analysis_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.assertion_error_cause_finder.AssertionErrorCauseFinder') as mock_assertion_error_cause_finder:
            mock_assertion_error_cause_finder.is_assertion_error.side_effect = [AnalysisDetails([False, 'scenario', None], "Error reading test case logs")]
            self.error_cause_finder.assertion_error_cause_finder = mock_assertion_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual('unknown', error_cause.why)
            self.assertIsNone(error_cause.information)
            self.assertEqual(['Assertions: Error reading test case logs'], error_cause.analysis_errors)

    def _test_detect_cause_with_image(self, on_right_page_response, on_previous_page_response, element_present_response, error_message_response, expected_cause, expected_why, expected_information, expected_analysis_error):
        with patch('snapshotServer.controllers.error_cause.image_error_cause_finder.ImageErrorCauseFinder') as mock_image_error_cause_finder:
            mock_image_error_cause_finder.is_on_the_right_page.side_effect = on_right_page_response
            mock_image_error_cause_finder.is_on_the_previous_page.side_effect = on_previous_page_response
            mock_image_error_cause_finder.is_error_message_displayed_in_last_step.side_effect = error_message_response
            mock_image_error_cause_finder.is_element_present_on_last_step.side_effect = element_present_response
            self.error_cause_finder.image_error_cause_finder = mock_image_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(expected_cause, error_cause.cause)
            self.assertEqual(expected_why, error_cause.why)
            self.assertEqual(expected_information, error_cause.information)
            self.assertEqual(expected_analysis_error, error_cause.analysis_errors)

    def test_detect_cause_on_right_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, 'bad_locator', "Element seems to be present, check the locator", [])

    def test_detect_cause_on_right_page_error_element_present(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, ["No element provided"])],
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, 'unknown', None, ['Element presence: No element provided'])

    def test_detect_cause_on_right_page_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, "some error")],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, 'bad_locator', 'Element seems to be present, check the locator', ["On same page: some error"])

    def test_detect_cause_on_previous_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, 'unknown', None, [])

    def test_detect_cause_on_previous_page_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, "some error")],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.APPLICATION, 'unknown_page', 'Page is unknown', ["On previous page: some error"])

    def test_detect_cause_on_other_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.APPLICATION, 'unknown_page', "Page is unknown", [])

    def test_detect_cause_element_not_on_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, 'unknown', None, [])

    def test_detect_cause_error_message(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(["an error message"], None)],
                                           Cause.APPLICATION, 'error_message', ["an error message"], [])

    def test_detect_cause_error_message_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails([], "some error")],
                                           Cause.SCRIPT, 'bad_locator', 'Element seems to be present, check the locator', ["Error message: some error"])

    def test_detect_cause_js_error(self):
        with patch('snapshotServer.controllers.error_cause.js_error_cause_finder.JsErrorCauseFinder') as mock_js_error_cause_finder:
            mock_js_error_cause_finder.has_javascript_errors.side_effect = [AnalysisDetails(['log1', 'log2'], None)]
            self.error_cause_finder.js_error_cause_finder = mock_js_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual('javascript_error', error_cause.why)
            self.assertEqual(['log1', 'log2'], error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_js_error_with_analysis_error(self):
        with patch('snapshotServer.controllers.error_cause.js_error_cause_finder.JsErrorCauseFinder') as mock_js_error_cause_finder:
            mock_js_error_cause_finder.has_javascript_errors.side_effect = [AnalysisDetails([], 'some error for js')]
            self.error_cause_finder.js_error_cause_finder = mock_js_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual('unknown', error_cause.why)
            self.assertIsNone(error_cause.information)
            self.assertEqual(['JS error: some error for js'], error_cause.analysis_errors)

    def test_detect_cause_network_error(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails(['error1', 'error2'], None)]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual('network_error', error_cause.why)
            self.assertEqual("On right page: Consult HAR file", error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_network_error_previous_page(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder, \
            patch('snapshotServer.controllers.error_cause.image_error_cause_finder.ImageErrorCauseFinder') as mock_image_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails(['error1', 'error2'], None)]
            mock_image_error_cause_finder.is_on_the_previous_page.side_effect = [AnalysisDetails(True, None)]
            mock_image_error_cause_finder.is_on_the_right_page.side_effect = [AnalysisDetails(False, None)]
            mock_image_error_cause_finder.is_error_message_displayed_in_last_step.side_effect = [AnalysisDetails([], None)]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            self.error_cause_finder.image_error_cause_finder = mock_image_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual('network_error', error_cause.why)
            self.assertEqual("On previous page: Consult HAR file", error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_network_slowness(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails([], None)]
            mock_network_error_cause_finder.has_network_slowness.side_effect = [AnalysisDetails(['slow1', 'slow2'], None)]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual('environment', error_cause.cause)
            self.assertEqual('network_slowness', error_cause.why)
            self.assertEqual("On right page: Consult HAR file", error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_network_error_with_analysis_error(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails([], "some error")]
            mock_network_error_cause_finder.has_network_slowness.side_effect = [AnalysisDetails([], "some error2")]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual('unknown', error_cause.why)
            self.assertIsNone(error_cause.information)
            self.assertEqual(["some error", "some error2"], error_cause.analysis_errors)