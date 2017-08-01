from django import forms

from snapshotServer.models import TestSession, TestStep, TestCaseInSession


class ImageUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    stepResult = forms.IntegerField()
    
    def clean(self):
        super().clean()
        try:
            self.cleaned_data['stepResult']
        except KeyError as e:
            raise forms.ValidationError("stepResult must be specified")
          
        try:
            TestStep.objects.get(id=self.cleaned_data['stepResult'])
        except Exception as e:
            raise forms.ValidationError("stepResult not found")