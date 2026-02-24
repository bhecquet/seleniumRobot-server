from snapshotServer.controllers.error_cause import Reason, Cause
from snapshotServer.models import StepResult, Error
from snapshotServer.tests import SnapshotTestCase


class TestError(SnapshotTestCase):

    fixtures = ['error_cause_finder_commons.yaml', 'error_cause_finder_test_ok.yaml', 'error_cause_finder_test_ko.yaml']

    def setUp(self):
        self.step_result = StepResult.objects.get(pk=11)

    def _test_friendly_message(self, cause: str, caused_by: str, cause_details: str, expected_message: str):
        error = Error(stepResult=self.step_result)
        error.cause = cause
        error.causedBy = caused_by
        error.causeDetails = cause_details
        error.save()
        self.assertEqual(expected_message, error.friendly_message())


    def test_friendly_message_assertion_on_step(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.STEP_ASSERTION_ERROR,
                                    'some details on error',
                                    "Assertion on step 'openPage with args: (https://myapp/jenkins/, )': some details on error")

    def test_friendly_message_assertion_on_scenario(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.SCENARIO_ASSERTION_ERROR,
                                    'some details on error',
                                    "Assertion in script: some details on error")

    def test_friendly_message_error_message(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.ERROR_MESSAGE,
                                    'message 1',
                                    "Application displays error message: 'message 1'")

    def test_friendly_message_unknown_page(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.UNKNOWN_PAGE,
                                    'some details on error',
                                    "Page where we land is unknown (not expected nor the previous page), check if application has changed")

    def test_friendly_message_javascript_error(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.JAVASCRIPT_ERROR,
                                    'some details on error',
                                    "Javascript error occurred, it may have cause the application to break, check detailed results")

    def test_friendly_message_network_error(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.NETWORK_ERROR,
                                    'some details on error',
                                    "Network error during failed step 'openPage with args: (https://myapp/jenkins/, )': some details on error")

    def test_friendly_message_unknown_application_error(self):
        self._test_friendly_message(Cause.APPLICATION,
                                    Reason.UNKNOWN,
                                    'some details on error',
                                    "Application error with 'unknown_error' and 'some details on error'")

    def test_friendly_message_element_not_found(self):
        self._test_friendly_message(Cause.SCRIPT,
                                    Reason.BAD_LOCATOR,
                                    'some details on error',
                                    "Element not found, but element seems to be present on page, check the locator")

    def test_friendly_message_unknown_cause(self):
        self._test_friendly_message(Cause.SCRIPT,
                                    Reason.UNKNOWN,
                                    'some details on error',
                                    "No clear cause has been found, check script")

    def test_friendly_message_unknown_script_cause(self):
        self._test_friendly_message(Cause.SCRIPT,
                                    'other_cause',
                                    'some details on error',
                                    "Script error with 'other_cause'")


    def test_friendly_message_network_slowness(self):
        self._test_friendly_message(Cause.ENVIRONMENT,
                                    Reason.NETWORK_SLOWNESS,
                                    'some details on error',
                                    "Network slowness during failed step 'openPage with args: (https://myapp/jenkins/, )': some details on error")

    def test_friendly_message_unknown_environment_error(self):
        self._test_friendly_message(Cause.ENVIRONMENT,
                                    Reason.UNKNOWN,
                                    'some details on error',
                                    "Environment error with 'other_error' and 'some details on error'")


    def test_friendly_message_unknown(self):
        self._test_friendly_message(Cause.UNKNOWN,
                                    Reason.UNKNOWN,
                                    'some details on error',
                                    "other - other_cause")

