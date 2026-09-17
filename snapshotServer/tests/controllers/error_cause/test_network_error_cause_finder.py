from django.test import TestCase

from commonsServer import preferences
from snapshotServer.controllers.error_cause.network_error_cause_finder import NetworkErrorCauseFinder
from snapshotServer.models import StepResult, TestCaseInSession, TestSession, TestEnvironment, Version


class TestNetworkErrorCauseFinder(TestCase):

    fixtures = ['error_cause_finder/error_cause_finder_commons.yaml',
                'error_cause_finder/error_cause_finder_test_ok.yaml',
                'error_cause_finder/error_cause_finder_test_ko.yaml']

    def tearDown(self):
        preferences.invalidate_pref_cache('NETWORK_SLOWNESS_RATIO')
        preferences.invalidate_pref_cache('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS')

    def _add_history(self, mean_xhr=100.0, mean_html=100.0, mean_js=100.0, mean_image=100.0, count=3,
                      environment_id=1, version_id=1, step_id=3):
        """
        Create 'count' additional executions of the same test case (testCase=1), with a StepResult on the given
        step (pk=3, the one that failed in test case in session 11, by default) so that NetworkErrorCauseFinder
        has some history to compare with.
        By default, history is created with the same environment (pk=1) and version (pk=1) as the current
        execution (test case in session 11 / session 11), but this can be overridden to simulate history coming
        from a different environment or version, which should not be taken into account
        """
        for i in range(count):
            test_session = TestSession.objects.get(pk=1)
            test_session.pk = None
            test_session.sessionId = f"history-{i}-{environment_id}-{version_id}-{step_id}"
            test_session.environment_id = environment_id
            test_session.version_id = version_id
            test_session.save()

            tcis = TestCaseInSession.objects.get(pk=1)
            tcis.pk = None
            tcis.session = test_session
            tcis.save()

            StepResult.objects.create(step_id=step_id,
                                       testCase=tcis,
                                       result=True,
                                       duration=100,
                                       meanXhrLoadTimes=mean_xhr,
                                       meanHtmlLoadTimes=mean_html,
                                       meanJsLoadTimes=mean_js,
                                       meanImageLoadTimes=mean_image)

    def _add_previous_execution(self, step_id=3, network_errors=None, status='SUCCESS', environment_id=1, version_id=1, pk=5):
        """
        Create a single additional execution of the same test case (testCase=1), with a StepResult on the given
        step, carrying the given networkErrors, so that has_network_errors() has a previous execution to compare
        with when checking whether an error was already present before.
        The created execution uses a pk lower than the current one (test case in session 11), so that it is
        correctly considered as a "previous" execution and not a "later" one.
        :param status: overall status of the created execution (TestCaseInSession.status), 'SUCCESS' by default
        :param pk: pk to use for both the TestSession and TestCaseInSession created, must be different for each
                    call within the same test and lower than 11 (the current test case in session's pk)
        :return: the created StepResult
        """
        test_session = TestSession.objects.get(pk=1)
        test_session.pk = pk
        test_session.sessionId = f"previous-{step_id}-{status}-{environment_id}-{version_id}-{pk}"
        test_session.environment_id = environment_id
        test_session.version_id = version_id
        test_session.save()

        tcis = TestCaseInSession.objects.get(pk=1)
        tcis.pk = pk
        tcis.session = test_session
        tcis.status = status
        tcis.save()

        return StepResult.objects.create(step_id=step_id,
                                          testCase=tcis,
                                          result=status == 'SUCCESS',
                                          duration=100,
                                          networkErrors=network_errors or [])

    def test_no_failed_step(self):
        """
        If no step failed, there is nothing to analyze
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_not_enough_history(self):
        """
        If there is not enough history for the same step, we cannot detect slowness
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()

        self._add_history(count=1)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_no_slowness_detected(self):
        """
        Current mean load times are similar to historical ones => no slowness
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 110.0
        failed_step_result.meanHtmlLoadTimes = 105.0
        failed_step_result.meanJsLoadTimes = 95.0
        failed_step_result.meanImageLoadTimes = 100.0
        failed_step_result.save()

        self._add_history(mean_xhr=100.0, mean_html=100.0, mean_js=100.0, mean_image=100.0)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_detected_on_xhr(self):
        """
        Current XHR mean load time is far higher than the historical average => slowness detected
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.meanHtmlLoadTimes = 100.0
        failed_step_result.meanJsLoadTimes = 100.0
        failed_step_result.meanImageLoadTimes = 100.0
        failed_step_result.save()

        self._add_history(mean_xhr=100.0, mean_html=100.0, mean_js=100.0, mean_image=100.0)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn("XHR", analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_detected_on_several_resource_types(self):
        """
        Several resource types are slow at the same time => several errors reported
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.meanHtmlLoadTimes = 5000.0
        failed_step_result.meanJsLoadTimes = 100.0
        failed_step_result.meanImageLoadTimes = 100.0
        failed_step_result.save()

        self._add_history(mean_xhr=100.0, mean_html=100.0, mean_js=100.0, mean_image=100.0)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual(2, len(analysis_details.errors))
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_not_searched_on_previous_step_when_found_on_failed_step(self):
        """
        When slowness is already detected on the failed step, the previous step should not be checked, even if
        it is also abnormally slow
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=3)

        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.meanXhrLoadTimes = 5000.0
        previous_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=2)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn("step '%s'" % failed_step_result.step.name, analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_detected_on_previous_step_when_not_found_on_failed_step(self):
        """
        When no slowness is found on the failed step, the previous step should also be checked, as a network
        slowness occurring during a step may only break the following step
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 100.0
        failed_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=3)

        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.meanXhrLoadTimes = 5000.0
        previous_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=2)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn("step '%s'" % previous_step_result.step.name, analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_no_slowness_when_neither_failed_nor_previous_step_are_slow(self):
        """
        When neither the failed step nor the previous one are abnormally slow, no error is reported
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 100.0
        failed_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=3)

        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.meanXhrLoadTimes = 100.0
        previous_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=2)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_no_previous_step_when_failed_step_is_first_step(self):
        """
        When the failed step is the first step of the test, there is no previous step to fall back on: this
        must not raise an error
        """
        StepResult.objects.filter(pk__in=[12, 13]).update(result=True)

        first_step_result = StepResult.objects.get(pk=11)
        first_step_result.result = False
        first_step_result.meanXhrLoadTimes = 100.0
        first_step_result.save()
        self._add_history(mean_xhr=100.0, step_id=1)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_unmeasured_values_are_ignored(self):
        """
        When mean load time has not been measured (-1.0, the default value), it should not be considered
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = -1.0
        failed_step_result.save()

        self._add_history(mean_xhr=100.0)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_small_difference_is_ignored(self):
        """
        Even if the ratio is respected, a small absolute difference (in ms) should not trigger a false positive
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 15.0
        failed_step_result.save()

        self._add_history(mean_xhr=5.0)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_history_with_different_environment_is_ignored(self):
        """
        History coming from a different environment than the current execution (test case in session 11 is on
        environment pk=1) must not be used for comparison, even if it would otherwise be significant enough to
        detect slowness
        """
        other_environment = TestEnvironment.objects.create(name="PROD")

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()

        # history on a different environment: should be excluded, leaving not enough history to compare with
        self._add_history(mean_xhr=100.0, environment_id=other_environment.pk)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_history_with_different_version_is_ignored(self):
        """
        History coming from a different version than the current execution (test case in session 11 is on
        version pk=1) must not be used for comparison, even if it would otherwise be significant enough to
        detect slowness
        """
        other_version = Version.objects.create(application_id=1, name="2.0")

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()

        # history on a different version: should be excluded, leaving not enough history to compare with
        self._add_history(mean_xhr=100.0, version_id=other_version.pk)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_still_detected_with_mixed_environments_and_versions(self):
        """
        When history contains both matching (same environment/version) and non-matching executions, only the
        matching ones must be used. Non-matching executions here have a mean time as high as the current one:
        if they were wrongly taken into account, they would raise the average enough to mask the slowness
        """
        other_environment = TestEnvironment.objects.create(name="PROD")
        other_version = Version.objects.create(application_id=1, name="2.0")

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()

        # matching history: low average, so the current value is clearly abnormal => slowness should be detected
        self._add_history(mean_xhr=100.0, count=3)
        # non-matching history (different environment / version): high values that would mask slowness if included
        self._add_history(mean_xhr=5000.0, count=5, environment_id=other_environment.pk)
        self._add_history(mean_xhr=5000.0, count=5, version_id=other_version.pk)

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn("XHR", analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_ratio_preference_is_used(self):
        """
        Raising the NETWORK_SLOWNESS_RATIO preference should prevent detection of a slowness that would
        otherwise be flagged with the default ratio
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 1000.0
        failed_step_result.save()

        # average = 100, current = 1000 => ratio of 10, above the default 1.5 ratio => slowness detected by default
        self._add_history(mean_xhr=100.0)

        # make sure default preferences are already synced to database before overriding the value (see
        # comment in test_slowness_min_difference_preference_is_used for details)
        preferences.get_preference('NETWORK_SLOWNESS_RATIO')
        preferences.get_preference('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS')

        preferences.set_preference('NETWORK_SLOWNESS_RATIO', '15')
        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_slowness_min_difference_preference_is_used(self):
        """
        Raising the NETWORK_SLOWNESS_MIN_DIFFERENCE_MS preference should prevent detection of a slowness that
        would otherwise be flagged with the default minimum difference
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.meanXhrLoadTimes = 5000.0
        failed_step_result.save()

        # average = 100, current = 5000 => far above the default ratio and default 200ms difference
        self._add_history(mean_xhr=100.0)

        # make sure default preferences are already synced to database before overriding the value, otherwise
        # the sync (triggered by reading NETWORK_SLOWNESS_RATIO from has_network_slowness) would recreate the
        # NETWORK_SLOWNESS_MIN_DIFFERENCE_MS row and invalidate the cached override set below
        preferences.get_preference('NETWORK_SLOWNESS_RATIO')
        preferences.get_preference('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS')

        preferences.set_preference('NETWORK_SLOWNESS_MIN_DIFFERENCE_MS', '10000')
        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_slowness()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_no_network_errors(self):
        """
        If neither the failed step nor the previous one recorded network errors, nothing is reported
        """
        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_errors_on_failed_step(self):
        """
        Network errors recorded on the failed step itself are reported
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('https://myapp/api/data', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_errors_on_previous_step(self):
        """
        Network errors recorded on the step preceding the failed one are also reported, as a network error on a
        step may only break the following step
        """
        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.networkErrors = [
            {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
        ]
        previous_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('https://myapp/api/save', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_errors_not_searched_on_previous_step_when_found_on_failed_step(self):
        """
        When network errors are found on the failed step, the previous step should not be checked, even if it
        also has network errors
        """
        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.networkErrors = [
            {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
        ]
        previous_step_result.save()

        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
            {'url': 'https://myapp/api/aborted', 'status': None, 'statusText': None},
        ]
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(2, len(analysis_details.errors))
        self.assertIn('https://myapp/api/data', analysis_details.errors[0])
        self.assertIn('https://myapp/api/aborted', analysis_details.errors[1])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_with_no_response(self):
        """
        A network error with no response at all (status is None) is reported with a specific wording
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/aborted', 'status': None, 'statusText': None},
        ]
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('https://myapp/api/aborted', analysis_details.errors[0])
        self.assertIn('no response', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_errors_when_failed_step_is_first_step(self):
        """
        When the failed step is the first step of the test, there is no previous step to look at: only the
        failed step's own network errors should be reported, without raising an error
        """
        StepResult.objects.filter(pk__in=[12, 13]).update(result=True)

        first_step_result = StepResult.objects.get(pk=11)
        first_step_result.result = False
        first_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        first_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('https://myapp/api/data', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_no_failed_step_for_network_errors(self):
        """
        If no step failed, there is nothing to analyze
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.result = True
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual([], analysis_details.errors)
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_already_present_on_previous_successful_execution(self):
        """
        When the same error (same URL, same status) was already present on the same step during the previous
        successful execution of the test, it must be mentioned in the description
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        self._add_previous_execution(step_id=3, network_errors=[
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('already present on the previous successful execution', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_not_present_on_previous_successful_execution(self):
        """
        When the previous successful execution did not have the same error, it must not be flagged as such
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        self._add_previous_execution(step_id=3, network_errors=[])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertNotIn('already present', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_with_different_status_on_previous_successful_execution_not_flagged(self):
        """
        An error on the same URL but with a different status code on the previous successful execution should
        not be considered as the same error
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        self._add_previous_execution(step_id=3, network_errors=[
            {'url': 'https://myapp/api/data', 'status': 500, 'statusText': 'Internal Server Error'},
        ])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertNotIn('already present', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_with_no_previous_execution_at_all(self):
        """
        When there is no previous execution at all for the failed step, the error should still be reported,
        without being flagged as already present, and without raising an error
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertNotIn('already present', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_with_no_previous_successful_execution(self):
        """
        When previous executions of the same step exist, but none of them succeeded overall, the error should
        still be reported, without being flagged as already present
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        self._add_previous_execution(step_id=3, status='FAILURE', network_errors=[
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertNotIn('already present', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_already_present_check_uses_correct_step(self):
        """
        When the error is found on the previous step (fallback case), it must be compared against the previous
        successful execution of THAT step, not the failed step
        """
        previous_step_result = StepResult.objects.get(pk=12)
        previous_step_result.networkErrors = [
            {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
        ]
        previous_step_result.save()

        # matching history on step 2 (the previous step): should be flagged as already present
        self._add_previous_execution(step_id=2, pk=5, network_errors=[
            {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
        ])
        # history on step 3 (the failed step, which has no error of its own here) must not interfere
        self._add_previous_execution(step_id=3, pk=6, network_errors=[
            {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
        ])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertIn('already present on the previous successful execution', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)

    def test_network_error_ignores_later_successful_execution(self):
        """
        A successful execution of the same test that happened AFTER the current one must not be considered when
        checking if the error was already present before: only executions that occurred before the current one
        (pk lower than 11) count as "previous"
        """
        failed_step_result = StepResult.objects.get(pk=13)
        failed_step_result.networkErrors = [
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ]
        failed_step_result.save()

        # a later execution (pk 20, higher than 11, the current test case in session) with the same error must
        # be ignored: it is not a "previous" execution
        self._add_previous_execution(step_id=3, pk=20, network_errors=[
            {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
        ])

        analysis_details = NetworkErrorCauseFinder(TestCaseInSession.objects.get(pk=11)).has_network_errors()
        self.assertEqual(1, len(analysis_details.errors))
        self.assertNotIn('already present', analysis_details.errors[0])
        self.assertIsNone(analysis_details.analysis_error)
