from django.urls import reverse

from pdf.tests import build_pdf
from pdf.tests.views.pdf_view_test_case import PdfViewTestCase


class TestPdfCompareResultView(PdfViewTestCase):

    def test_authentication_required(self):
        """RG-ACC-01: redirect to login when not authenticated"""
        url = reverse('pdf-compare-result')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={url}', response.url)

    def test_no_result_redirects_to_compare(self):
        """RG-RES-01: without result in session, redirect to comparison"""
        self.login()
        response = self.client.get(reverse('pdf-compare-result'))
        self.assertRedirects(response, reverse('pdf-compare'), fetch_redirect_response=False)

    def test_result_after_comparison(self):
        """RG-RES-02: result displayed with both PDFs retrieved from cache"""
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

    def test_debug_info_hidden_by_default_with_raw_response(self):
        """RG-RES-05: raw model response is in the page, hidden by default, behind a "Debug info" button"""
        self.login()
        session = self.client.session
        session['pdf_compare_result'] = {'differences': [], 'full_response': '{"raw": "model answer"}'}
        session.save()

        response = self.client.get(reverse('pdf-compare-result'))

        self.assertContains(response, 'id="debugInfoBtn"')
        self.assertContains(response, 'Debug info')
        self.assertContains(response, 'id="debugInfoContainer" style="display:none;"')
        # content is HTML-escaped inside the textarea
        self.assertContains(response, '{&quot;raw&quot;: &quot;model answer&quot;}')

    def test_debug_info_contains_full_response_of_comparison(self):
        """RG-RES-05: raw response of the comparator is displayed after a real comparison"""
        self.login()
        self.client.post(reverse('pdf-compare'), {'pdf_file_1': build_pdf(1, 'a.pdf'),
                                                  'pdf_file_2': build_pdf(1, 'b.pdf'),
                                                  'model': 'stub', 'user_prompt': ''})

        response = self.client.get(reverse('pdf-compare-result'))

        self.assertContains(response, 'Amount is different', count=2)  # difference table + raw response

    def test_result_with_expired_payload(self):
        """RG-RES-03: PDFs expired from cache, result is displayed without them"""
        self.login()
        session = self.client.session
        session['pdf_compare_result'] = {'differences': [], 'full_response': '{}'}
        session['pdf_compare_payload_token'] = 'expired'
        session.save()

        response = self.client.get(reverse('pdf-compare-result'))

        self.assertEqual(200, response.status_code)
        self.assertNotIn('left_pdf_src', response.context)
