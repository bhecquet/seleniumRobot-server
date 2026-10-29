from django.urls import reverse

from pdf.tests import build_pdf
from pdf.tests.views.pdf_view_test_case import PdfViewTestCase


class TestPdfCompareResultView(PdfViewTestCase):

    def test_authentication_required(self):
        url = reverse('pdf-compare-result')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={url}', response.url)

    def test_no_result_redirects_to_compare(self):
        self.login()
        response = self.client.get(reverse('pdf-compare-result'))
        self.assertRedirects(response, reverse('pdf-compare'), fetch_redirect_response=False)

    def test_result_after_comparison(self):
        self.login()
        self.client.post(reverse('pdf-compare'), {'pdf_file_1': build_pdf(1, 'a.pdf'),
                                                  'pdf_file_2': build_pdf(1, 'b.pdf'),
                                                  'model': 'stub', 'user_prompt': ''})
        response = self.client.get(reverse('pdf-compare-result'))

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'pdf/compare_result.html')
        self.assertEqual('a.pdf', response.context['left_pdf_name'])
        self.assertEqual('b.pdf', response.context['right_pdf_name'])
        self.assertTrue(response.context['left_pdf_src'].startswith('data:application/pdf;base64,'))

    def test_result_with_expired_payload(self):
        self.login()
        session = self.client.session
        session['pdf_compare_result'] = {'differences': [], 'full_response': '{}'}
        session['pdf_compare_payload_token'] = 'expired'
        session.save()

        response = self.client.get(reverse('pdf-compare-result'))

        self.assertEqual(200, response.status_code)
        self.assertNotIn('left_pdf_src', response.context)
