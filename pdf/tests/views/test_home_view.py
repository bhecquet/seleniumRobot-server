from django.urls import reverse

from pdf.tests.views.pdf_view_test_case import PdfViewTestCase


class TestPdfHomeView(PdfViewTestCase):

    def test_home(self):
        self.login()
        response = self.client.get(reverse('pdf-home'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'pdf/home.html')

    def test_authentication_required(self):
        url = reverse('pdf-home')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f'/accounts/login/?next={url}', response.url)
