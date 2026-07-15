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
        choices=[('mistral_doc', 'Mistral Document annotation'),
                 ('stub', 'Stub (for tests only)')]
    )

    user_prompt = forms.CharField(
        label='Additional instructions',
        required=False,
        help_text='Some information to give to model. E.g: exclude some differences, things to avoid, ... This will be added to request',
        widget=forms.Textarea
    )

    def clean_pdf_file_1(self):
        f = self.cleaned_data.get('pdf_file_1')
        if f and not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError('File must be PDF.')
        return f

    def clean_pdf_file_2(self):
        f = self.cleaned_data.get('pdf_file_2')
        if f and not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError('File must be PDF.')
        return f

