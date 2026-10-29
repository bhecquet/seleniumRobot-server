from django import forms


class PdfCompareForm(forms.Form):
    pdf_file_1 = forms.FileField(
        label='First PDF file',
        help_text='Select first PDF to compare',
        widget=forms.FileInput(attrs={'accept': 'application/pdf', 'class': 'form-control'})
    )
    pdf_file_2 = forms.FileField(
        label='Second PDF file',
        help_text='Select second PDF to compare',
        widget=forms.FileInput(attrs={'accept': 'application/pdf', 'class': 'form-control'})
    )

    model = forms.ChoiceField(
        label='Model to use',
        help_text='Select model to use for comparison',
        choices=[
            ('azure_ocr', 'Azure document comparator'),
            ('mistral_doc', 'Mistral Document annotation'),
             ('stub', 'Stub (for tests only)')
        ]
    )

    user_prompt = forms.CharField(
        label='Additional instructions',
        required=False,
        help_text='Some information to give to model. E.g: exclude some differences, things to avoid, ... This will be added to request',
        widget=forms.Textarea
    )

    def clean_pdf_file_1(self):
        return self._check_pdf(self.cleaned_data.get('pdf_file_1'))

    def clean_pdf_file_2(self):
        return self._check_pdf(self.cleaned_data.get('pdf_file_2'))

    @staticmethod
    def _check_pdf(f):
        """Check extension and content signature ('%PDF-' header, allowed in the first 1024 bytes)"""
        if not f:
            return f
        if not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError('File must be PDF.')
        f.seek(0)
        header = f.read(1024)
        f.seek(0)
        if b'%PDF-' not in header:
            raise forms.ValidationError('File content is not a PDF.')
        return f
