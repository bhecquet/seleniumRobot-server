from unittest.mock import patch

from django.test import TestCase

from snapshotServer.views.test_result_view import TestResultView


class TestKnowledgeBaseInTestResultView(TestCase):

    fixtures = [
        'error_cause_finder/error_cause_finder_commons.yaml',
        'error_cause_finder/error_cause_finder_test_ok.yaml',
        'error_cause_finder/error_cause_finder_test_ko.yaml',
    ]

    def create_view(self):
        view = TestResultView()
        view.kwargs = {
            'test_case_in_session_id': 11,
        }
        return view

    @patch(
        'snapshotServer.views.test_result_view.find_probable_cause'
    )
    def test_get_queryset_adds_suggested_cause(
            self,
            find_probable_cause_mock
    ):
        find_probable_cause_mock.return_value = {
            'cause': 'Le locator du bouton est obsolète',
            'count': 1,
            'total': 1,
        }

        view = self.create_view()
        step_snapshots = view.get_queryset()

        step_results_with_exception = [
            step_result
            for step_result in step_snapshots
            if 'exception' in step_result.details
        ]

        self.assertTrue(step_results_with_exception)
        self.assertTrue(find_probable_cause_mock.called)

        for step_result in step_results_with_exception:
            self.assertEqual(
                'Le locator du bouton est obsolète',
                step_result.details['suggestedCause'],
            )
            self.assertEqual(
                100,
                step_result.details['confidence'],
            )

    @patch(
        'snapshotServer.views.test_result_view.find_probable_cause'
    )
    def test_get_queryset_sets_none_when_no_cause_is_found(
            self,
            find_probable_cause_mock
    ):
        find_probable_cause_mock.return_value = None

        view = self.create_view()
        step_snapshots = view.get_queryset()

        step_results_with_exception = [
            step_result
            for step_result in step_snapshots
            if 'exception' in step_result.details
        ]

        self.assertTrue(step_results_with_exception)
        self.assertTrue(find_probable_cause_mock.called)

        for step_result in step_results_with_exception:
            self.assertIsNone(
                step_result.details['suggestedCause']
            )
            self.assertNotIn(
                'confidence',
                step_result.details,
            )

    @patch(
        'snapshotServer.views.test_result_view.find_probable_cause'
    )
    def test_get_queryset_continues_when_analyzer_raises_exception(
            self,
            find_probable_cause_mock
    ):
        find_probable_cause_mock.side_effect = RuntimeError(
            'Knowledge base unavailable'
        )

        view = self.create_view()
        step_snapshots = view.get_queryset()

        self.assertIsInstance(step_snapshots, dict)
        self.assertTrue(step_snapshots)
        self.assertTrue(find_probable_cause_mock.called)

        step_results_with_exception = [
            step_result
            for step_result in step_snapshots
            if 'exception' in step_result.details
        ]

        self.assertTrue(step_results_with_exception)

        for step_result in step_results_with_exception:
            self.assertIsNone(
                step_result.details['suggestedCause']
            )

    @patch(
        'snapshotServer.views.test_result_view.find_probable_cause'
    )
    def test_get_queryset_passes_expected_parameters_to_analyzer(
            self,
            find_probable_cause_mock
    ):
        find_probable_cause_mock.return_value = None

        view = self.create_view()
        step_snapshots = view.get_queryset()

        step_results_with_exception = [
            step_result
            for step_result in step_snapshots
            if 'exception' in step_result.details
        ]

        self.assertTrue(step_results_with_exception)

        first_step_result = step_results_with_exception[0]

        find_probable_cause_mock.assert_any_call(
            exception=first_step_result.details.get('exception'),
            testCase=first_step_result.testCase.testCase,
            testStep=first_step_result.step,
        )