'''
Unit tests for snapshotServer.forms.ImageForComparisonUploadForm and
ImageForComparisonUploadFormNoStorage
'''
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile

from snapshotServer.forms import ImageForComparisonUploadForm, \
    ImageForComparisonUploadFormNoStorage
from snapshotServer.models import Application, Version, TestEnvironment, \
    TestCase, TestStep, TestSession, TestCaseInSession, StepResult
from snapshotServer.tests import SnapshotTestCase


class TestImageForComparisonUploadForm(SnapshotTestCase):

    def setUp(self):
        super().setUp()

        self.application = Application(name='myapp')
        self.application.save()
        self.version = Version(application=self.application, name='1.0')
        self.version.save()
        self.environment = TestEnvironment(name='DEV')
        self.environment.save()
        self.test_case = TestCase(name='test upload', application=self.application)
        self.test_case.save()
        self.test_step = TestStep(name='Step 1')
        self.test_step.save()

        self.test_session = TestSession(sessionId='1234',
                                         version=self.version,
                                         browser='BROWSER:FIREFOX',
                                         environment=self.environment,
                                         compareSnapshot=True,
                                         date=datetime.datetime.now(),
                                         ttl=datetime.timedelta(days=0))
        self.test_session.save()
        self.test_case_in_session = TestCaseInSession(testCase=self.test_case, session=self.test_session)
        self.test_case_in_session.save()
        self.step_result = StepResult(step=self.test_step, testCase=self.test_case_in_session, result=True)
        self.step_result.save()

    def _get_image(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            return SimpleUploadedFile('engie.png', fp.read(), content_type='image/png')

    def test_form_valid_with_correct_data(self):
        """
        Form should be valid when all mandatory data are provided and stepResult exists
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_when_stepresult_does_not_exist(self):
        """
        Form should be invalid when the provided stepResult id does not correspond to any StepResult
        """
        form = ImageForComparisonUploadForm(data={'stepResult': 99999,
                                                    'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertFalse(form.is_valid())
        self.assertIn('stepResult not found', str(form.errors))

    def test_form_invalid_when_stepresult_missing(self):
        """
        Form should be invalid when stepResult is not provided (mandatory field)
        """
        form = ImageForComparisonUploadForm(data={'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertFalse(form.is_valid())

    def test_store_snapshot_is_true(self):
        """
        storeSnapshot should always be set to True for this form
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data['storeSnapshot'])

    def test_diff_tolerance_defaults_to_zero_when_not_provided(self):
        """
        diffTolerance should default to 0.0 when not provided
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['diffTolerance'], 0.0)

    def test_diff_tolerance_kept_when_provided(self):
        """
        diffTolerance provided value should be kept
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL',
                                                    'diffTolerance': 10.5},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['diffTolerance'], 10.5)

    def test_diff_tolerance_out_of_bounds_is_invalid(self):
        """
        diffTolerance must be between 0 and 100.
        As it is rejected at the field level, it is absent from cleaned_data, which makes
        the form clean() method raise a KeyError (existing behavior of the form).
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL',
                                                    'diffTolerance': 150},
                                             files={'image': self._get_image()})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn('diffTolerance', form.errors)

    def test_compare_invalid_value_defaults_to_true(self):
        """
        compare should default to 'true' when the provided value is not 'true' or 'false'
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'foo'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['compare'], 'FULL')

    def test_compare_false_value_kept(self):
        """
        compare value 'ZONES' should be kept as is
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'ZONES'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['compare'], 'ZONES')

    def test_exclude_zones_none_when_not_provided(self):
        """
        excludeZones should default to an empty list when not provided
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['excludeZones'], [])

    def test_exclude_zones_parsed_to_exclude_zone_objects(self):
        """
        excludeZones JSON should be converted to a list of ExcludeZone instances
        """
        form = ImageForComparisonUploadForm(data={'stepResult': self.step_result.id,
                                                    'name': 'img',
                                                    'compare': 'FULL',
                                                    'excludeZones': '[{"x": 1, "y": 2, "width": 3, "height": 4}]'},
                                             files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        exclude_zones = form.cleaned_data['excludeZones']
        self.assertEqual(len(exclude_zones), 1)
        self.assertEqual(exclude_zones[0].x, 1)
        self.assertEqual(exclude_zones[0].y, 2)
        self.assertEqual(exclude_zones[0].width, 3)
        self.assertEqual(exclude_zones[0].height, 4)


class TestImageForComparisonUploadFormNoStorage(SnapshotTestCase):

    def setUp(self):
        super().setUp()

        self.application = Application(name='myapp')
        self.application.save()
        self.version = Version(application=self.application, name='1.0')
        self.version.save()
        self.environment = TestEnvironment(name='DEV')
        self.environment.save()
        self.test_step = TestStep(name='Step 1')
        self.test_step.save()

    def _get_image(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            return SimpleUploadedFile('engie.png', fp.read(), content_type='image/png')

    def _get_data(self, **overrides):
        data = {'stepName': 'Step 1',
                'testCaseName': 'test upload',
                'versionId': self.version.id,
                'environmentId': self.environment.id,
                'browser': 'BROWSER:FIREFOX',
                'name': 'img',
                'compare': 'FULL'}
        data.update(overrides)
        return data

    def test_form_valid_with_correct_data(self):
        """
        Form should be valid when all mandatory data are provided
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_creates_test_case_when_not_existing(self):
        """
        A new TestCase should be created when it does not exist yet for the application
        """
        self.assertEqual(TestCase.objects.filter(name='test upload', application=self.application).count(), 0)

        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(TestCase.objects.filter(name='test upload', application=self.application).count(), 1)
        self.assertEqual(form.cleaned_data['testCase'].name, 'test upload')

    def test_form_reuses_existing_test_case(self):
        """
        An existing TestCase should be reused instead of creating a new one
        """
        existing_test_case = TestCase(name='test upload', application=self.application)
        existing_test_case.save()

        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(TestCase.objects.filter(name='test upload', application=self.application).count(), 1)
        self.assertEqual(form.cleaned_data['testCase'].id, existing_test_case.id)

    def test_form_creates_step_result_and_test_session(self):
        """
        A StepResult and its related TestSession / TestCaseInSession should be created
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)

        step_result = form.cleaned_data['stepResult']
        self.assertIsNotNone(step_result.id)
        self.assertEqual(step_result.step, self.test_step)
        self.assertTrue(step_result.result)

        test_session = form.cleaned_data['testSession']
        self.assertEqual(test_session.version, self.version)
        self.assertEqual(test_session.environment, self.environment)
        self.assertEqual(test_session.browser, 'BROWSER:FIREFOX')

    def test_store_snapshot_is_false(self):
        """
        storeSnapshot should always be set to False for this form
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data['storeSnapshot'])

    def test_form_invalid_when_version_does_not_exist(self):
        """
        Form validation should raise an error when versionId does not match any Version
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(versionId=99999), files={'image': self._get_image()})
        with self.assertRaises(Version.DoesNotExist):
            form.is_valid()

    def test_form_invalid_when_environment_does_not_exist(self):
        """
        Form validation should raise an error when environmentId does not match any TestEnvironment
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(environmentId=99999), files={'image': self._get_image()})
        with self.assertRaises(TestEnvironment.DoesNotExist):
            form.is_valid()

    def test_form_invalid_when_step_does_not_exist(self):
        """
        Form validation should raise an error when stepName does not match any TestStep
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(stepName='unknown step'), files={'image': self._get_image()})
        with self.assertRaises(TestStep.DoesNotExist):
            form.is_valid()

    def test_diff_tolerance_defaults_to_zero_when_not_provided(self):
        """
        diffTolerance should default to 0.0 when not provided
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['diffTolerance'], 0.0)

    def test_compare_invalid_value_defaults_to_true(self):
        """
        compare should default to 'FULL' when the provided value is not in COMPARE_OPTIONS
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(compare='foo'), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['compare'], 'FULL')

    def test_exclude_zones_none_when_not_provided(self):
        """
        excludeZones should default to an empty list when not provided
        """
        form = ImageForComparisonUploadFormNoStorage(data=self._get_data(), files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['excludeZones'], [])

    def test_exclude_zones_parsed_to_exclude_zone_objects(self):
        """
        excludeZones JSON should be converted to a list of ExcludeZone instances
        """
        form = ImageForComparisonUploadFormNoStorage(
            data=self._get_data(excludeZones='[{"x": 1, "y": 2, "width": 3, "height": 4}]'),
            files={'image': self._get_image()})
        self.assertTrue(form.is_valid(), form.errors)
        exclude_zones = form.cleaned_data['excludeZones']
        self.assertEqual(len(exclude_zones), 1)
        self.assertEqual(exclude_zones[0].x, 1)
        self.assertEqual(exclude_zones[0].y, 2)
        self.assertEqual(exclude_zones[0].width, 3)
        self.assertEqual(exclude_zones[0].height, 4)
