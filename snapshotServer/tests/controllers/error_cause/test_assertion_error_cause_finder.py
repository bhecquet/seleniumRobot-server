from django.test import TestCase

from snapshotServer.controllers.error_cause.assertion_error_cause_finder import AssertionErrorCauseFinder
from snapshotServer.models import StepResult, TestCaseInSession, Error


class TestAssertionErrorCauseFinder(TestCase):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def test_assertion_on_failed_step(self):
        """
        This test assumes there is a failed step and an error created for it
        error is an assertion error
        :return:
        """
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([True, 'step', "java.lang.AssertionError: expected [false] but <_> found [true]"], analysis_details.details)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_with_other_error_on_failed_step(self):
        error = Error.objects.get(pk=13)
        error.exception = "SomeException"
        error.errorMessage = "SomeException: an error message"
        error.save()
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([False, 'step', "SomeException: an error message"], analysis_details.details)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_without_error_on_failed_step(self):
        Error.objects.get(pk=13).delete()
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([False, 'step', None], analysis_details.details)
        self.assertIsNone(analysis_details.analysis_error)

    def test_assertion_on_test(self):
        """
        Assertion is on the test, not the step
        :return:
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([True, 'scenario', 'java.lang.AssertionError: expected [false] but <_> found [true]'], analysis_details.details)
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
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([False, 'scenario', 'SomeException'], analysis_details.details)
        self.assertIsNone(analysis_details.analysis_error)


    def test_assertion_on_test_invalid_stack(self):

        tcis = TestCaseInSession.objects.get(pk=11)
        tcis.stacktrace = '{"stacktrace"}'
        tcis.save()

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()
        analysis_details = AssertionErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).is_assertion_error()
        self.assertEqual([False, 'scenario', None], analysis_details.details)
        self.assertEqual("Error reading test case logs: Expecting ':' delimiter: line 1 column 14 (char 13)", analysis_details.analysis_error)

