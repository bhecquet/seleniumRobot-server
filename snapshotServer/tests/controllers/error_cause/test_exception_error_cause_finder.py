from django.test import TestCase

from snapshotServer.controllers.error_cause.exception_error_cause_finder import ExceptionErrorCauseFinder
from snapshotServer.models import StepResult, TestCaseInSession, Error


class TestAssertionErrorCauseFinder(TestCase):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def test_assertion_on_failed_step(self):
        """
        This test assumes there is a failed step and an error created for it
        error is an assertion error
        :return:
        """
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('assertion', analysis_details.error_type)
        self.assertEqual('java.lang.AssertionError: expected [false] but <_> found [true]', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_nosuchelementexception_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "org.openqa.selenium.NoSuchElementException"
        error.errorMessage = "org.openqa.selenium.NoSuchElementException: an error message"
        error.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertTrue(analysis_details.search_cause)
        self.assertEqual('search_element', analysis_details.error_type)
        self.assertEqual('org.openqa.selenium.NoSuchElementException: an error message', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_notcurrentpageexception_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "com.seleniumtests.customexception.NotCurrentPageException"
        error.errorMessage = "com.seleniumtests.customexception.NotCurrentPageException: an error message"
        error.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertTrue(analysis_details.search_cause)
        self.assertEqual('search_element', analysis_details.error_type)
        self.assertEqual('com.seleniumtests.customexception.NotCurrentPageException: an error message', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_imagesearchexception_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "com.seleniumtests.customexception.ImageSearchException"
        error.errorMessage = "com.seleniumtests.customexception.ImageSearchException: an error message"
        error.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertTrue(analysis_details.search_cause)
        self.assertEqual('search_element', analysis_details.error_type)
        self.assertEqual('com.seleniumtests.customexception.ImageSearchException: an error message', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_scenarioexception_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "com.seleniumtests.customexception.ScenarioException"
        error.errorMessage = "com.seleniumtests.customexception.ScenarioException: an error message"
        error.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('scenario', analysis_details.error_type)
        self.assertEqual('com.seleniumtests.customexception.ScenarioException: an error message', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_other_exception_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "SomeException"
        error.errorMessage = "SomeException: an error message"
        error.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('exception', analysis_details.error_type)
        self.assertEqual('SomeException: an error message', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_without_error_on_failed_step(self):
        Error.objects.get(pk=13).delete()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('unknown', analysis_details.error_type)
        self.assertEqual('', analysis_details.error_message)
        self.assertEqual('step', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_on_test(self):
        """
        Assertion is on the test, not the step
        :return:
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('assertion', analysis_details.error_type)
        self.assertEqual('java.lang.AssertionError: expected [false] but <_> found [true]', analysis_details.error_message)
        self.assertEqual('scenario', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_on_test_other_error(self):
        """
        Assertion is on the test, not the step and it's not an AssertionError
        :return:
        """
        tcis = TestCaseInSession.objects.get(pk=11)
        tcis.stacktrace = '{"stacktrace": "SomeException\\nstackLin1", "logs": "some logs"}'
        tcis.save()

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('unknown', analysis_details.error_type)
        self.assertEqual('SomeException', analysis_details.error_message)
        self.assertEqual('scenario', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_on_test_scenarioexception(self):
        """
        Assertion is on the test, not the step and it's not an AssertionError
        :return:
        """
        tcis = TestCaseInSession.objects.get(pk=11)
        tcis.stacktrace = '{"stacktrace": "class com.seleniumtests.customexception.ScenarioException: Snapshot comparison failed"}'
        tcis.save()

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('scenario', analysis_details.error_type)
        self.assertEqual('class com.seleniumtests.customexception.ScenarioException: Snapshot comparison failed', analysis_details.error_message)
        self.assertEqual('scenario', analysis_details.location)
        self.assertIsNone(analysis_details.analysis_error)


    def test_assertion_on_test_invalid_stack(self):

        tcis = TestCaseInSession.objects.get(pk=11)
        tcis.stacktrace = '{"stacktrace"}'
        tcis.save()

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = ExceptionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).analyze_error()
        self.assertFalse(analysis_details.search_cause)
        self.assertEqual('unknown', analysis_details.error_type)
        self.assertEqual('', analysis_details.error_message)
        self.assertEqual('scenario', analysis_details.location)
        self.assertEqual("Error reading test case logs: Expecting ':' delimiter: line 1 column 14 (char 13)", analysis_details.analysis_error)

