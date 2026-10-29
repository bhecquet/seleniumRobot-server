from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference
from pdf.models import PdfRequestLog
from pdf.tests import build_pdf
from pdf.tests.views.pdf_view_test_case import PdfViewTestCase
from pdf.views.compare_view import PdfCompareView


class TestPdfCompareView(PdfViewTestCase):

    def _post(self, **overrides):
        data = {'pdf_file_1': build_pdf(1, 'a.pdf'), 'pdf_file_2': build_pdf(2, 'b.pdf'),
                'model': 'stub', 'user_prompt': ''}
        data.update(overrides)
        return self.client.post(reverse('pdf-compare'), data)

    def test_get_authentication_required(self):
        url = reverse('pdf-compare')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={url}', response.url)

    def test_post_authentication_required(self):
        response = self._post()
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        self.assertNotIn('pdf_compare_result', self.client.session)

    def test_get_displays_form(self):
        self.login()
        response = self.client.get(reverse('pdf-compare'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'pdf/compare.html')
        self.assertIn('form', response.context)

    def test_post_invalid_form(self):
        self.login()
        response = self._post(model='unknown')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'pdf/compare.html')
        self.assertIn('model', response.context['form'].errors)

    def test_post_stub_redirects_to_result(self):
        self.login()
        response = self._post()

        log = PdfRequestLog.objects.get()
        self.assertEqual(self.user, log.user)
        self.assertEqual(PdfRequestLog.TYPE_COMPARISON, log.request_type)
        self.assertEqual(PdfRequestLog.ORIGIN_UI, log.origin)
        self.assertEqual(1, log.nb_pages_1)
        self.assertEqual(2, log.nb_pages_2)
        self.assertEqual('', log.user_instructions)
        self.assertTrue(log.success)
        self.assertIsNotNone(log.date)

        self.assertRedirects(response, reverse('pdf-compare-result'), fetch_redirect_response=False)
        result = self.client.session['pdf_compare_result']
        self.assertEqual('a.pdf', result['file1_name'])
        self.assertEqual('b.pdf', result['file2_name'])
        self.assertEqual(1, result['nb_pages_1'])
        self.assertEqual(2, result['nb_pages_2'])
        self.assertEqual([{'page': 1, 'details': 'Amount is different', 'location': 'first part'}],
                         result['differences'])

        token = self.client.session['pdf_compare_payload_token']
        payload = cache.get(f'{PdfCompareView.cache_prefix}:{token}')
        self.assertEqual('a.pdf', payload['left_name'])
        self.assertTrue(payload['right_content'].startswith(b'%PDF'))

    @mock.patch('pdf.views.compare_view.AzureOcrComparator')
    def test_post_azure_model(self, comparator_class):
        comparator_class.return_value.compare.return_value = ComparisonResult([Difference(1, 'l', 'd')])
        self.login()
        response = self._post(model='azure_ocr', user_prompt='ignore totals')

        self.assertRedirects(response, reverse('pdf-compare-result'), fetch_redirect_response=False)
        prompt = comparator_class.call_args.args[0]
        self.assertIn('ignore totals', prompt)
        self.assertIn('IGNORE', prompt)
        # raw user instructions are logged, not the wrapped prompt
        self.assertEqual('ignore totals', PdfRequestLog.objects.get().user_instructions)

    @mock.patch('pdf.views.compare_view.MistralDocComparator')
    def test_post_mistral_model(self, comparator_class):
        comparator_class.return_value.compare.return_value = ComparisonResult([])
        self.login()
        response = self._post(model='mistral_doc')

        self.assertRedirects(response, reverse('pdf-compare-result'), fetch_redirect_response=False)
        comparator_class.assert_called_once_with('')

    @mock.patch('pdf.views.compare_view.StubComparator')
    def test_post_comparison_error(self, comparator_class):
        comparator_class.return_value.compare.side_effect = Exception('boom')
        self.login()
        with self.assertLogs('pdf.views.compare_view', level='ERROR'):
            response = self._post()

        self.assertEqual(200, response.status_code)
        self.assertIn('boom', response.context['error'])
        self.assertNotIn('pdf_compare_result', self.client.session)
        self.assertEqual(0, PdfRequestLog.objects.filter(success=True).count())
        log = PdfRequestLog.objects.get()
        self.assertFalse(log.success)
        self.assertEqual('boom', log.error_message)
        self.assertEqual((1, 2), (log.nb_pages_1, log.nb_pages_2))

    def test_post_unreadable_pdf_is_logged(self):
        self.login()
        bad = SimpleUploadedFile('bad.pdf', b'not a pdf')
        with self.assertLogs('pdf.views.compare_view', level='WARNING'):
            self._post(pdf_file_1=bad, model='stub')

        log = PdfRequestLog.objects.get()
        self.assertIsNone(log.nb_pages_1)
        self.assertEqual(2, log.nb_pages_2)

    def test_post_purges_old_logs(self):
        old = PdfRequestLog.objects.create(request_type=PdfRequestLog.TYPE_COMPARISON, nb_pages_1=1)
        PdfRequestLog.objects.filter(pk=old.pk).update(date=timezone.now() - timedelta(days=400))
        self.login()

        self._post()
        self.assertFalse(PdfRequestLog.objects.filter(pk=old.pk).exists())
        self.assertEqual(1, PdfRequestLog.objects.count())

    def test_post_purge_throttled(self):
        """
        As a purge has already been done through the first 'post', no new purge should be done before 1 hour
        :return:
        """
        self.login()
        self._post()
        old = PdfRequestLog.objects.create(request_type=PdfRequestLog.TYPE_COMPARISON, nb_pages_1=1)
        PdfRequestLog.objects.filter(pk=old.pk).update(date=timezone.now() - timedelta(days=400))

        self._post()
        self.assertTrue(PdfRequestLog.objects.filter(pk=old.pk).exists())

    def test_post_invalid_form_not_logged(self):
        self.login()
        self._post(model='unknown')
        self.assertEqual(0, PdfRequestLog.objects.count())

    def test_build_pdf_data_uri(self):
        self.assertIsNone(PdfCompareView._build_pdf_data_uri(b''))
        self.assertEqual('data:application/pdf;base64,YWJj', PdfCompareView._build_pdf_data_uri(b'abc'))
