from django import forms

from snapshotServer.models import StepResult


class ImageUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    stepResult = forms.IntegerField()
    name = forms.CharField()
    compare = forms.CharField()
    
    def clean(self):
        super().clean()
        try:
            self.cleaned_data['stepResult']
        except KeyError as e:
            raise forms.ValidationError("stepResult must be specified")
          
        try:
            StepResult.objects.get(id=self.cleaned_data['stepResult'])
        except Exception as e:
            raise forms.ValidationError("stepResult not found")