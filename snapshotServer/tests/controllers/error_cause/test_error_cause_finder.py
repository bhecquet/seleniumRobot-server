import time
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db.models import Q
from django.test import TestCase, override_settings

from snapshotServer.controllers.error_cause import AnalysisDetails, Cause, Reason
from snapshotServer.controllers.error_cause.exception_error_cause_finder import ExceptionErrorCauseFinder, \
    ExceptionAnalysisDetails
from snapshotServer.controllers.error_cause.error_cause_finder import ErrorCauseFinder
from snapshotServer.controllers.error_cause.image_error_cause_finder import ImageErrorCauseFinder
from snapshotServer.controllers.error_cause.js_error_cause_finder import JsErrorCauseFinder
from snapshotServer.controllers.error_cause.network_error_cause_finder import NetworkErrorCauseFinder
from snapshotServer.models import TestCaseInSession, Error, StepResult
from snapshotServer.tests.controllers.error_cause.test_image_error_cause_finder import Response, MockedOpenWebUiClient, \
    TestImageErrorCauseFinder

from commonsServer.tests.test_api import TestApi
from variableServer.models import Application


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

class TestErrorCauseFinder(TestApi):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def setUp(self):
        Application.objects.get(pk=1).save()
        self.error_cause_finder = ErrorCauseFinder(TestCaseInSession.objects.get(pk=11), FakeJsErrorCauseFinder(), FakeImageErrorCauseFinder(), FakeExceptionErrorCauseFinder(), FakeNetworkErrorCauseFinder())

    @override_settings(OPEN_WEBUI_URL='')
    def test_detect_cause_with_test_ok(self):
        self.assertIsNone(ErrorCauseFinder(TestCaseInSession.objects.get(pk=1)).detect_cause())

    def test_detect_cause_with_assertion_on_step(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'step', 'assertion', 'some assertion', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual(Reason.STEP_ASSERTION_ERROR, error_cause.why)
            self.assertEqual('some assertion', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_search_element_error_on_step(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(True, 'step', 'search_element', 'element not found', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.UNKNOWN, error_cause.cause)
            self.assertEqual(Reason.UNKNOWN, error_cause.why)
            self.assertEqual(None, error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_other_exception_on_step(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'step', 'exception', 'some exception', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual(Reason.UNKNOWN, error_cause.why)
            self.assertEqual('some exception', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_without_error_found_on_step(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'step', 'unknown', '', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual(Reason.UNKNOWN, error_cause.why)
            self.assertEqual('', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_assertion_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'scenario', 'assertion', 'some assertion', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual(Reason.SCENARIO_ASSERTION_ERROR, error_cause.why)
            self.assertEqual('some assertion', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_scenarioexception_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'scenario', 'scenario', 'some scenario exception', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual(Reason.SCENARIO_ERROR, error_cause.why)
            self.assertEqual('some scenario exception', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_error_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'scenario', 'scenario', 'some exception', None)]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual(Reason.SCENARIO_ERROR, error_cause.why)
            self.assertEqual('some exception', error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_with_error_analysis_on_scenario(self):
        with patch('snapshotServer.controllers.error_cause.exception_error_cause_finder.ExceptionErrorCauseFinder') as mock_exception_error_cause_finder:
            mock_exception_error_cause_finder.analyze_error.side_effect = [ExceptionAnalysisDetails(False, 'scenario', 'unknown', '', "Error reading test case logs")]
            self.error_cause_finder.exception_error_cause_finder = mock_exception_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.SCRIPT, error_cause.cause)
            self.assertEqual(Reason.SCENARIO_ERROR, error_cause.why)
            self.assertEqual('', error_cause.information)
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
                                           Cause.SCRIPT, Reason.BAD_LOCATOR, "Element seems to be present, check the locator", [])

    def test_detect_cause_on_right_page_error_element_present(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, "No element provided")],
                                           [AnalysisDetails([], None)],
                                           Cause.UNKNOWN, Reason.UNKNOWN, None, ['Element presence: No element provided'])

    def test_detect_cause_on_right_page_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, "some error")],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails([], None)],
                                           Cause.SCRIPT, Reason.BAD_LOCATOR, 'Element seems to be present, check the locator', ["On same page: some error"])

    def test_detect_cause_on_previous_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.UNKNOWN, Reason.UNKNOWN, None, [])

    def test_detect_cause_on_previous_page_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, "some error")],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.APPLICATION, Reason.UNKNOWN_PAGE, 'Page is unknown', ["On previous page: some error"])

    def test_detect_cause_on_other_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(False, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)], # useless
                                           [AnalysisDetails([], None)],
                                           Cause.APPLICATION, Reason.UNKNOWN_PAGE, "Page is unknown", [])

    def test_detect_cause_element_not_on_page(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails([], None)],
                                           Cause.UNKNOWN, Reason.UNKNOWN, None, [])

    def test_detect_cause_error_message(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails(["an error message"], None)],
                                           Cause.APPLICATION, Reason.ERROR_MESSAGE, ["an error message"], [])

    def test_detect_cause_error_message_with_analysis_error(self):
        self._test_detect_cause_with_image([AnalysisDetails(True, None)],
                                           [AnalysisDetails(False, None)],
                                           [AnalysisDetails(True, None)],
                                           [AnalysisDetails([], "some error")],
                                           Cause.SCRIPT, Reason.BAD_LOCATOR, 'Element seems to be present, check the locator', ["Error message: some error"])

    def test_detect_cause_js_error(self):
        with patch('snapshotServer.controllers.error_cause.js_error_cause_finder.JsErrorCauseFinder') as mock_js_error_cause_finder:
            mock_js_error_cause_finder.has_javascript_errors.side_effect = [AnalysisDetails(['log1', 'log2'], None)]
            self.error_cause_finder.js_error_cause_finder = mock_js_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual(Reason.JAVASCRIPT_ERROR, error_cause.why)
            self.assertEqual(['log1', 'log2'], error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_js_error_with_analysis_error(self):
        with patch('snapshotServer.controllers.error_cause.js_error_cause_finder.JsErrorCauseFinder') as mock_js_error_cause_finder:
            mock_js_error_cause_finder.has_javascript_errors.side_effect = [AnalysisDetails([], 'some error for js')]
            self.error_cause_finder.js_error_cause_finder = mock_js_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.UNKNOWN, error_cause.cause)
            self.assertEqual(Reason.UNKNOWN, error_cause.why)
            self.assertIsNone(error_cause.information)
            self.assertEqual(['JS error: some error for js'], error_cause.analysis_errors)

    def test_detect_cause_network_error(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails(['error1', 'error2'], None)]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.APPLICATION, error_cause.cause)
            self.assertEqual(Reason.NETWORK_ERROR, error_cause.why)
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
            self.assertEqual(Reason.NETWORK_ERROR, error_cause.why)
            self.assertEqual("On previous page: Consult HAR file", error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_network_slowness(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails([], None)]
            mock_network_error_cause_finder.has_network_slowness.side_effect = [AnalysisDetails(['slow1', 'slow2'], None)]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.ENVIRONMENT, error_cause.cause)
            self.assertEqual(Reason.NETWORK_SLOWNESS, error_cause.why)
            self.assertEqual("On right page: Consult HAR file", error_cause.information)
            self.assertEqual([], error_cause.analysis_errors)

    def test_detect_cause_network_error_with_analysis_error(self):
        with patch('snapshotServer.controllers.error_cause.network_error_cause_finder.NetworkErrorCauseFinder') as mock_network_error_cause_finder:
            mock_network_error_cause_finder.has_network_errors.side_effect = [AnalysisDetails([], "some error")]
            mock_network_error_cause_finder.has_network_slowness.side_effect = [AnalysisDetails([], "some error2")]
            self.error_cause_finder.network_error_cause_finder = mock_network_error_cause_finder
            error_cause = self.error_cause_finder.detect_cause()
            self.assertEqual(Cause.UNKNOWN, error_cause.cause)
            self.assertEqual(Reason.UNKNOWN, error_cause.why)
            self.assertIsNone(error_cause.information)
            self.assertEqual(["some error", "some error2"], error_cause.analysis_errors)


    @override_settings(OPEN_WEBUI_URL='', RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True)
    def test_stepresult_analyze_test_run_result_ko_on_update_full_process(self):
        """
        When error in step, error cause detection is performed
        This test will go deep, using LLM mock
        """

        failed_test_end_stacktrace = """
    {
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
                        "idImage": 111,
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
                "files": [
                    {
                        "name": "Video capture",
                        "id": 112,
                        "type": "file"
                    },
                    {
                        "name": "Browser log file",
                        "id": 113,
                        "type": "file"
                    }
                ],
                "position": 3,
                "actions": [
                    {
                        "messageType": "LOG",
                        "name": "Test is KO with error: class java.lang.AssertionError: expected [false] but <> found [true]",
                        "type": "message"
                    },
                    {
                        "messageType": "WARNING",
                        "name": "[NOT RETRYING] max retry count (0) reached",
                        "type": "message"
                    }
                ],
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


        test_case_in_session = TestCaseInSession.objects.get(pk=11)
        image_error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        image_error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()

        error_cause_finder_instance = ErrorCauseFinder(test_case_in_session=test_case_in_session, image_error_cause_finder=image_error_cause_finder)

        with patch('requests.post') as mock_request, patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder', autospec=True) as mock_error_cause_finder:
            mock_request.side_effect = [Response(200, TestImageErrorCauseFinder.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")]

            mock_error_cause_finder.return_value = error_cause_finder_instance

            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.patch('/snapshot/api/stepresult/14/' , data={'stacktrace': failed_test_end_stacktrace})
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, len(Error.objects.all()))
            time.sleep(1)
            error = Error.objects.all()[0]
            self.assertEqual("application", error.cause)
            self.assertEqual('step_assertion_error', error.causedBy)
            self.assertEqual('java.lang.AssertionError: expected [false] but <_> found [true]', error.causeDetails)


    @override_settings(OPEN_WEBUI_URL='', RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True)
    def test_stepresult_analyze_test_run_result_ko_on_update_full_process2(self):
        """
        When error in step, error cause detection is performed
        This test will go deep, using LLM mock
        """

        failed_step_stacktrace = """{
                "exception": "org.openqa.selenium.NoSuchElementException",
                "date": "Wed Oct 25 18:06:07 CEST 2023",
                "failed": true,
                "type": "step",
                "duration": 5539,
                "snapshots": [
                    {
                        "idHtml": 106,
                        "displayInReport": true,
                        "name": "drv:main",
                        "idImage": 107,
                        "failed": false,
                        "position": 0,
                        "type": "snapshot",
                        "title": "Current Window: S'identifier [Jenkins]",
                        "snapshotCheckType": "NONE",
                        "url": "https://jenkins/jenkins/loginError",
                        "timestamp": 1698257174035
                    },
                    {
                        "idHtml": null,
                        "displayInReport": true,
                        "name": "Step beginning state",
                        "idImage": 108,
                        "failed": false,
                        "position": 1,
                        "type": "snapshot",
                        "snapshotCheckType": "NONE_REFERENCE",
                        "timestamp": 1698257175623
                    },
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
                "action": "getErrorMessage<>",
                "files": [],
                "position": 2,
                "actions": [
                    {
                        "exception": "org.openqa.selenium.NoSuchElementException",
                        "durationToExclude": 0,
                        "origin": "pic.jenkins.tests.selenium.webpage.LoginPage",
                        "failed": true,
                        "type": "action",
                        "name": "sendKeys on TextFieldElement user, by={By.id: j_username} with args: (true, true, [foo,], )",
                        "action": "sendKeys",
                        "position": 0,
                        "elementDescription": "text field described by 'user'",
                        "elementType": "text field",
                        "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement user, by={By.id: j_username}] from page 'pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                        "timestamp": 1771506843252,
                        "element": "user"
                    },
                    {
                        "messageType": "WARNING",
                        "name": "Warning: Searched element [TextFieldElement user, by={By.id: j_username}] from page 'pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\nFor documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#nosuchelementexception\\nBuild info: version: '4.38.0', revision: '6b412e825c*'\\nSystem info: os.name: 'Windows 11', os.arch: 'amd64', os.version: '10.0', java.version: '21.0.4'\\nDriver info: driver.version: unknown\\nat covea.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody6(LoginPage.java:42)\\nat covea.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody8(LoginPage.java:40)\\nat covea.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid(LoginPage.java:40)",
                        "type": "message"
                    }
                ],
                "timestamp": 1698257167869,
                "status": "FAILED",
                "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement user, by={By.id: j_username}] from page 'pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                "harCaptures": []
            }
        """

        failed_test_end_stacktrace = """
    {
                "exception": "class org.openqa.selenium.NoSuchElementException",
                "date": "Wed Oct 25 18:06:14 CEST 2023",
                "failed": true,
                "type": "step",
                "duration": 277,
                "snapshots": [
                    {
                        "idHtml": 110,
                        "displayInReport": true,
                        "name": "drv:main",
                        "idImage": 111,
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
                "action": "Test end",
                "files": [
                    {
                        "name": "Video capture",
                        "id": 112,
                        "type": "file"
                    },
                    {
                        "name": "Browser log file",
                        "id": 113,
                        "type": "file"
                    }
                ],
                "position": 3,
                "actions": [
                    {
                        "messageType": "LOG",
                        "name": "Test is KO with error: class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement Text, by={By.id: text___}] from page 'com.seleniumtests.it.driver.support.pages.DriverTestPage' could not be found",
                        "type": "message"
                    },
                    {
                        "messageType": "WARNING",
                        "name": "[NOT RETRYING] max retry count (0) reached",
                        "type": "message"
                    }
                ],
                "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement Text, by={By.id: text___}] from page 'com.seleniumtests.it.driver.support.pages.DriverTestPage' could not be found",
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

        test_case_in_session = TestCaseInSession.objects.get(pk=11)
        image_error_cause_finder = ImageErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        image_error_cause_finder.llm_connector.open_web_ui_client = MockedOpenWebUiClient()

        error_cause_finder_instance = ErrorCauseFinder(test_case_in_session=test_case_in_session, image_error_cause_finder=image_error_cause_finder)

        with (patch('snapshotServer.controllers.llm_connector.requests.post') as mock_request,
              patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder', autospec=True) as mock_error_cause_finder):
            mock_request.side_effect = [Response(200, TestImageErrorCauseFinder.openwebui_message_template % "```json\\n{\\n  \\\"explanation\\\": \\\"\\n    Some explanation\\n  \\\",\\n  \\\"error_messages\\\": [\\n    \\\"Bad user name\\\"\\n  ]\\n}\\n```")]

            mock_error_cause_finder.return_value = error_cause_finder_instance

            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self.client.patch('/snapshot/api/stepresult/13/' , data={'stacktrace': failed_step_stacktrace})
            response = self.client.patch('/snapshot/api/stepresult/14/' , data={'stacktrace': failed_test_end_stacktrace})
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, len(Error.objects.all()))
            time.sleep(1)
            error = Error.objects.all()[0]
            self.assertEqual("application", error.cause)
            self.assertEqual('error_message', error.causedBy)
            self.assertEqual('Bad user name', error.causeDetails)
