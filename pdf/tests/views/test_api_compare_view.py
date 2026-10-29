from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from pdf.controllers.comparison import ComparisonError
from pdf.models import PdfRequestLog
from pdf.tests import build_pdf

COMPARATOR = 'pdf.controllers.comparison.comparison_service.MistralDocComparator'


class TestPdfCompareApiView(APITestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('user', password='pwd')
        self.url = reverse('pdf-api-compare')

    def _post(self, **overrides):
        data = {
            'reference': build_pdf(2, 'ref.pdf'),
            'file': build_pdf(3, 'new.pdf'),
            'model': 'stub',
        }
        data.update(overrides)
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.post(self.url, data, format='multipart')

    def test_unauthenticated_rejected(self):
        """RG-API-02: an unauthenticated call is rejected and nothing is logged"""
        response = self._post()
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(PdfRequestLog.objects.count(), 0)

    def test_authenticated_user_without_permission_accepted(self):
        """RG-API-03: any authenticated user can call the API, without specific permission"""
        self.client.force_authenticate(self.user)
        self.assertEqual(self._post().status_code, 200)

    def test_response_format(self):
        """RG-API-01, RG-API-04: response is JSON with 'differences' (location, details, page) and 'duration'"""
        self.client.force_authenticate(self.user)
        response = self._post()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body.keys()), {'differences', 'duration'})
        self.assertIsInstance(body['duration'], float)
        self.assertGreaterEqual(body['duration'], 0)
        self.assertTrue(len(body['differences']) > 0)
        for difference in body['differences']:
            self.assertEqual(set(difference.keys()), {'location', 'details', 'page'})

    def test_missing_reference(self):
        """RG-API-05: 'reference' file is mandatory"""
        self.client.force_authenticate(self.user)
        response = self._post(reference=None)
        self.assertEqual(response.status_code, 400)
        self.assertIn('reference', response.json()['errors'])

    def test_missing_file(self):
        """RG-API-05: 'file' is mandatory"""
        self.client.force_authenticate(self.user)
        response = self._post(file=None)
        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.json()['errors'])

    def test_non_pdf_file_rejected(self):
        """RG-API-06: files must have a .pdf extension"""
        self.client.force_authenticate(self.user)
        response = self._post(file=build_pdf(1, 'new.txt'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.json()['errors'])

    def test_non_pdf_content_rejected(self):
        """RG-API-06: files named .pdf must really contain a PDF"""
        self.client.force_authenticate(self.user)
        for name in ('reference', 'file'):
            response = self._post(**{name: SimpleUploadedFile('x.pdf', b'not a pdf')})
            self.assertEqual(response.status_code, 400)
            self.assertIn(name, response.json()['errors'])

    def test_invalid_model_rejected(self):
        """RG-API-07: model must be one of the supported models"""
        self.client.force_authenticate(self.user)
        response = self._post(model='unknown')
        self.assertEqual(response.status_code, 400)
        self.assertIn('model', response.json()['errors'])

    def test_missing_model_rejected(self):
        """RG-API-07: model is mandatory"""
        self.client.force_authenticate(self.user)
        response = self._post(model=None)
        self.assertEqual(response.status_code, 400)
        self.assertIn('model', response.json()['errors'])

    def test_invalid_input_not_logged(self):
        """RG-API-05, RG-API-10: a request rejected by validation is not compared and not logged"""
        self.client.force_authenticate(self.user)
        self._post(model='unknown')
        self.assertEqual(PdfRequestLog.objects.count(), 0)

    @mock.patch(COMPARATOR)
    def test_instructions_transmitted_to_model(self, comparator_class):
        """RG-API-08: optional instructions are sent to the model, wrapped as untrusted"""
        comparator_class.return_value.compare.return_value.serialize.return_value = {
            'differences': [], 'full_response': '{}'}
        self.client.force_authenticate(self.user)
        response = self._post(model='mistral_doc', instructions='ignore footer')
        self.assertEqual(response.status_code, 200)
        prompt = comparator_class.call_args[0][0]
        self.assertIn('ignore footer', prompt)
        self.assertIn('IGNORE', prompt)

    def test_instructions_optional(self):
        """RG-API-08: instructions are not mandatory"""
        self.client.force_authenticate(self.user)
        self.assertEqual(self._post().status_code, 200)

    def test_comparison_logged(self):
        """RG-API-09: a successful comparison is logged with origin 'api', user, page counts and instructions"""
        self.client.force_authenticate(self.user)
        self._post(instructions='some text')
        log = PdfRequestLog.objects.get()
        self.assertEqual(log.origin, PdfRequestLog.ORIGIN_API)
        self.assertEqual(log.request_type, PdfRequestLog.TYPE_COMPARISON)
        self.assertEqual(log.user, self.user)
        self.assertEqual((log.nb_pages_1, log.nb_pages_2), (2, 3))
        self.assertEqual(log.user_instructions, 'some text')
        self.assertTrue(log.success)

    @mock.patch(COMPARATOR)
    def test_failed_comparison(self, comparator_class):
        """RG-API-09, RG-API-11: a failing comparison returns a 500 error and is logged as failed"""
        comparator_class.return_value.compare.side_effect = ComparisonError('model down')
        self.client.force_authenticate(self.user)
        with self.assertLogs('pdf.controllers.comparison.comparison_service', level='ERROR'):
            response = self._post(model='mistral_doc')
        self.assertEqual(response.status_code, 500)
        self.assertIn('model down', response.json()['error'])
        log = PdfRequestLog.objects.get()
        self.assertFalse(log.success)
        self.assertEqual(log.origin, PdfRequestLog.ORIGIN_API)
        self.assertIn('model down', log.error_message)
