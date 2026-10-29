from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from pdf.forms import PdfCompareForm
from pdf.tests import build_pdf


class TestPdfCompareForm(SimpleTestCase):

    def _form(self, file1=None, file2=None, model='stub', prompt=''):
        return PdfCompareForm(
            {'model': model, 'user_prompt': prompt},
            {'pdf_file_1': file1 or build_pdf(name='a.pdf'), 'pdf_file_2': file2 or build_pdf(name='b.PDF')})

    def test_valid(self):
        self.assertTrue(self._form().is_valid())

    def test_prompt_optional(self):
        self.assertTrue(self._form(prompt='').is_valid())

    def test_invalid_extension_file_1(self):
        form = self._form(file1=SimpleUploadedFile('a.txt', b'x'))
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file_1', form.errors)

    def test_invalid_extension_file_2(self):
        form = self._form(file2=SimpleUploadedFile('b.docx', b'x'))
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file_2', form.errors)

    def test_invalid_model(self):
        form = self._form(model='unknown')
        self.assertFalse(form.is_valid())
        self.assertIn('model', form.errors)

    def test_missing_files(self):
        form = PdfCompareForm({'model': 'stub'}, {})
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file_1', form.errors)
        self.assertIn('pdf_file_2', form.errors)
