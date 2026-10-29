from django.urls import reverse

from pdf.tests.views.pdf_view_test_case import PdfViewTestCase


class TestPdfValidateView(PdfViewTestCase):

    def test_validate(self):
        self.login()
        response = self.client.get(reverse('pdf-validate'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'pdf/validate.html')

    def test_authentication_required(self):
        url = reverse('pdf-validate')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={url}', response.url)
