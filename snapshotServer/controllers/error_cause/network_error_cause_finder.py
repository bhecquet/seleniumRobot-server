from statistics import mean
from typing import Optional

from commonsServer import preferences
from snapshotServer.models import StepResult, TestStep

class NetworkAnalysisDetails:

    def __init__(self, errors: list, analysis_error: Optional[str]):
        self.errors = errors
        self.analysis_error = analysis_error


class NetworkErrorCauseFinder:

    # fields of StepResult holding the mean load time for each resource type, with a human friendly label
    MEAN_LOAD_TIME_FIELDS = {
        'meanXhrLoadTimes': 'XHR',
        'meanHtmlLoadTimes': 'HTML',
        'meanJsLoadTimes': 'JS',
        'meanImageLoadTimes': 'image',
    }

    # minimum number of other executions needed to consider the historical average as reliable
    MIN_HISTORY_SIZE = 3

    # number of previous executions of the same test / step to consider when computing the historical average
    HISTORY_SIZE = 20

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session
        self.failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False)\
            .exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')


    def _find_previous_successful_step_result(self, step_result: StepResult) -> Optional[StepResult]:
        """
        Find the most recent StepResult for the same step, same test case, same version and same environment as
        the given step result, coming from a test execution that succeeded overall (TestCaseInSession.status ==
        'SUCCESS') and that occurred before the current test execution (later executions of the same test must
        not be considered as "previous").
        :return: the matching StepResult, or None if no such execution exists
        """

        return StepResult.objects.filter(
            step=step_result.step,
            testCase__session__version=self.test_case_in_session.session.version,
            testCase__session__environment=self.test_case_in_session.session.environment,
            testCase__testCase=self.test_case_in_session.testCase,
            testCase__status='SUCCESS',
            testCase__pk__lt=self.test_case_in_session.pk
        ).order_by('-pk').first()

    def get_network_errors_for_step(self, step_result: StepResult) -> list:
        """
        Build a description for each network error (requests with no response, or a 4xx / 5xx response) stored
        in StepResult.networkErrors for the given step result.
        If the same error (same URL, same status) was already present on the same step during the previous
        successful execution of the test, it is mentioned in the description, as this may indicate the error is
        not the actual cause of the current failure.
        This method can be called for any step result, whatever its own result (success or failure).
        :return: a list containing a description of each network error found on the step
        """

        previous_successful_step_result = self._find_previous_successful_step_result(step_result)
        previous_errors = (previous_successful_step_result.networkErrors or []) if previous_successful_step_result else []

        errors = []
        for network_error in step_result.networkErrors or []:
            if network_error.get('status'):
                description = "failed with status %s %s" % (network_error.get('status'), network_error.get('statusText') or '')
            else:
                description = "got no response"

            already_present = any(
                previous_error.get('url') == network_error.get('url') and previous_error.get('status') == network_error.get('status')
                for previous_error in previous_errors
            )
            if already_present:
                description += " (already present on the previous successful execution of this step)"

            errors.append(
                "Network error on step '%s': request to '%s' %s"
                % (step_result.step.name, network_error.get('url'), description.strip())
            )

        return errors

    def has_network_errors(self) -> NetworkAnalysisDetails:
        """
        Check network errors (requests with no response, or a 4xx / 5xx response) stored in StepResult.networkErrors
        for the failed step of the current test execution.
        If no network error is found on the failed step, the previous step is also checked, as a network error
        occurring during a step may only break the following step (e.g.: a resource fails to load in step N, but
        the failure is only visible/detected in step N+1).
        Errors that were already present on the same step during the previous successful execution of the test
        (same version, same environment) are flagged as such, since they may not be the actual cause of the
        current failure.
        :return: a NetworkAnalysisDetails whose 'errors' list contains a description of each network error found
                 on the failed step, or on the previous one if none was found on the failed step
        """

        if not self.failed_step_result:
            return NetworkAnalysisDetails([], None)

        try:
            current_step_result = self.failed_step_result[0]

            errors = self.get_network_errors_for_step(current_step_result)

            if not errors:
                previous_step_result = StepResult.objects.filter(testCase=self.test_case_in_session,
                                                                   pk__lt=current_step_result.pk).order_by('-pk').first()
                if previous_step_result:
                    errors = self.get_network_errors_for_step(previous_step_result)

            return NetworkAnalysisDetails(errors, None)
        except Exception as e:
            return NetworkAnalysisDetails([], "Error detecting network errors: " + str(e))

    def get_network_slowness_for_step(self, step_result: StepResult, slowness_ratio: Optional[float] = None,
                                       slowness_min_difference_ms: Optional[float] = None) -> list:
        """
        Compare mean network load times (XHR, HTML, JS, image) of the given step result to the ones observed on
        other executions of the same step, for the same test case, same version and same environment.
        This method can be called for any step result, whatever its own result (success or failure).
        :param slowness_ratio: ratio above which a load time is considered abnormal, read from the
                                NETWORK_SLOWNESS_RATIO preference if not provided
        :param slowness_min_difference_ms: minimum absolute difference (ms) above which a load time is
                                            considered abnormal, read from the NETWORK_SLOWNESS_MIN_DIFFERENCE_MS
                                            preference if not provided
        :return: a list containing a description of each resource type for which slowness has been detected
        """

        if slowness_ratio is None:
            slowness_ratio = float(preferences.get_preference('NETWORK_SLOWNESS_RATIO'))
        if slowness_min_difference_ms is None:
            slowness_min_difference_ms = float(preferences.get_preference('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS'))

        # look at other executions of the same step, for the same test case, excluding the current one
        other_step_results = StepResult.objects.filter(
            step=step_result.step,
            testCase__session__version=self.test_case_in_session.session.version,
            testCase__session__environment=self.test_case_in_session.session.environment,
            testCase__testCase=self.test_case_in_session.testCase
        ).exclude(testCase=self.test_case_in_session).order_by('-pk')[:self.HISTORY_SIZE]

        errors = []
        for field_name, label in self.MEAN_LOAD_TIME_FIELDS.items():
            current_value = getattr(step_result, field_name)
            if current_value is None or current_value < 0:
                continue

            historical_values = [value for value in
                                  (getattr(other_step_result, field_name) for other_step_result in other_step_results)
                                  if value is not None and value >= 0]

            if len(historical_values) < self.MIN_HISTORY_SIZE:
                continue

            average = mean(historical_values)

            # a step is considered slow, for a given resource type, if its mean load time is both:
            # - greater than NETWORK_SLOWNESS_RATIO times the average mean load time observed on other
            #   executions of the same step
            # - greater than the average mean load time observed on other executions of the same step, by
            #   more than NETWORK_SLOWNESS_MIN_DIFFERENCE_MS (to avoid flagging tiny, insignificant differences)
            if (current_value > average * slowness_ratio
                    and current_value - average > slowness_min_difference_ms):
                errors.append(
                    "%s load time on step '%s' is abnormally high: %.2f ms (average on last %d executions: %.2f ms)"
                    % (label, step_result.step.name, current_value, len(historical_values), average)
                )

        return errors

    def has_network_slowness(self) -> NetworkAnalysisDetails:
        """
        Compare mean network load times (XHR, HTML, JS, image) of the failed step of the current test execution
        to the ones observed on other executions of the same step, for the same test case.
        If load times are abnormally higher than usual, the step (and so the test) is considered to suffer from
        network slowness.
        If no slowness is found on the failed step, the previous step is also checked, as a network slowness
        occurring during a step may only break the following step.
        :return: a NetworkAnalysisDetails whose 'errors' list contains a description of each resource type for
                 which slowness has been detected
        """

        if not self.failed_step_result:
            return NetworkAnalysisDetails([], None)

        try:
            current_step_result = self.failed_step_result[0]
            slowness_ratio = float(preferences.get_preference('NETWORK_SLOWNESS_RATIO'))
            slowness_min_difference_ms = float(preferences.get_preference('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS'))

            errors = self.get_network_slowness_for_step(current_step_result, slowness_ratio, slowness_min_difference_ms)

            if not errors:
                previous_step_result = StepResult.objects.filter(testCase=self.test_case_in_session,
                                                                   pk__lt=current_step_result.pk).order_by('-pk').first()
                if previous_step_result:
                    errors = self.get_network_slowness_for_step(previous_step_result, slowness_ratio, slowness_min_difference_ms)

            return NetworkAnalysisDetails(errors, None)
        except Exception as e:
            return NetworkAnalysisDetails([], "Error detecting network slowness: " + str(e))