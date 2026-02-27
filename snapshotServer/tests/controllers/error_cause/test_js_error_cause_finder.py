
from django.test import TestCase, override_settings
from django.conf import settings

from django.core.files import File as DjangoFile

from snapshotServer.controllers.error_cause.js_error_cause_finder import JsErrorCauseFinder
from snapshotServer.models import TestCaseInSession, StepResult, File, TestSession


class TestJsErrorCauseFinder(TestCase):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def setUp(self):
        with open(settings.MEDIA_ROOT + "/documents/browser_logs.txt", "w") as logs:
            logs.write('\n'.join(["[2023-10-25T18:06:07.869Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)",
                                  "[2023-10-25T18:06:07.969Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)"]))

    def test_analyze_javascript_logs_for_chrome(self):

        test_session = TestSession.objects.get(pk=11)
        test_session.browser = "BROWSER:CHROME"
        test_session.save()
        with open(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", "w") as logs:
            logs.write('\n'.join(["[2023-10-25T18:06:06.869Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)",
                                  "[2023-10-25T18:06:07.870Z] [SEVERE] some error",
                                  "[2023-10-25T18:06:08.869Z] [WARNING] some warning",
                                  "[2023-10-25T18:06:09.869Z] [INFO] some INFO",
                                  "[2023-10-25T18:06:10.869Z] [SEVERE] some other error"]))

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder._analyze_javascript_logs(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", 1698257167869)
        self.assertEqual(2, len(analysis_details.details))
        self.assertEqual("[2023-10-25T18:06:07.870Z] [SEVERE] some error", analysis_details.details[0])
        self.assertEqual("[2023-10-25T18:06:10.869Z] [SEVERE] some other error", analysis_details.details[1])


    def test_analyze_javascript_logs_missing_file(self):

        test_session = TestSession.objects.get(pk=11)
        test_session.browser = "BROWSER:CHROME"
        test_session.save()

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder._analyze_javascript_logs(settings.MEDIA_ROOT + "/documents/browser__missing_logs.txt", 1698257167869)
        self.assertEqual(0, len(analysis_details.details))
        self.assertTrue(analysis_details.analysis_error.startswith("Error reading log file: "))

    def test_analyze_javascript_logs_for_edge(self):

        test_session = TestSession.objects.get(pk=11)
        test_session.browser = "BROWSER:EDGE"
        test_session.save()
        with open(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", "w") as logs:
            logs.write('\n'.join(["[2023-10-25T18:06:06.869Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)",
                                  "[2023-10-25T18:06:07.870Z] [SEVERE] some error",
                                  "[2023-10-25T18:06:08.869Z] [WARNING] some warning",
                                  "[2023-10-25T18:06:09.869Z] [INFO] some INFO",
                                  "[2023-10-25T18:06:10.869Z] [SEVERE] some other error"]))

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder._analyze_javascript_logs(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", 1698257167869)
        self.assertEqual(2, len(analysis_details.details))
        self.assertEqual("[2023-10-25T18:06:07.870Z] [SEVERE] some error", analysis_details.details[0])
        self.assertEqual("[2023-10-25T18:06:10.869Z] [SEVERE] some other error", analysis_details.details[1])

    def test_analyze_javascript_logs_for_firefox(self):

        test_session = TestSession.objects.get(pk=11)
        test_session.browser = "BROWSER:FIREFOX"
        test_session.save()
        with open(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", "w") as logs:
            logs.write('\n'.join(["[2023-10-25T18:06:06.869Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)"]))

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder._analyze_javascript_logs(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", 1698257167869)
        self.assertEqual(0, len(analysis_details.details))
        self.assertEqual("Only chrome / Edge logs can be analyzed", analysis_details.analysis_error)

    def test_has_javascript_error(self):
        test_session = TestSession.objects.get(pk=11)
        test_session.browser = "BROWSER:CHROME"
        test_session.save()

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder.has_javascript_errors()
        self.assertEqual(1, len(analysis_details.details))
        self.assertIsNone(analysis_details.analysis_error)

    def test_has_javascript_error_missing_browser_logs(self):
        with open(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", "w") as logs:
            logs.write('\n'.join(["[2023-10-25T18:06:06.869Z] [SEVERE] https://jenkins/ - Failed to load resource: the server responded with a status of 403 (Forbidden)"]))
        with open(settings.MEDIA_ROOT + "/documents/browser_logs2.txt", "r") as logs:
            log_file = File.objects.get(pk=113)
            log_file.file = DjangoFile(logs, name="browser_logs2.txt")
            log_file.save()

            log_file.file = None
            log_file.save()

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder.has_javascript_errors()
        self.assertEqual(0, len(analysis_details.details))
        self.assertEquals("Error reading step details for analysis: The 'file' attribute has no file associated with it.", analysis_details.analysis_error)

    def test_has_javascript_error_no_browser_log_file(self):
        last_step_result = StepResult.objects.get(pk=14)
        last_step_result.stacktrace = """{
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
                "harCaptures": []
            }"""
        last_step_result.save()

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder.has_javascript_errors()
        self.assertEqual(0, len(analysis_details.details))
        self.assertEqual("No browser logs to analyze", analysis_details.analysis_error)

    def test_has_javascript_error_no_failed_step(self):
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result=True
        failed_step_result.save()

        error_cause_finder = JsErrorCauseFinder(TestCaseInSession.objects.get(pk=11))
        analysis_details = error_cause_finder.has_javascript_errors()
        self.assertEqual(0, len(analysis_details.details))
        self.assertEqual("No 'Test end' step where logs can be found", analysis_details.analysis_error)
