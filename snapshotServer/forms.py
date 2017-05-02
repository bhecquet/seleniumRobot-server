from django import forms

from snapshotServer.models import TestSession, TestStep


class ImageUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    step = forms.IntegerField()
    browser = forms.CharField()
    sessionId = forms.CharField()
    
    def clean(self):
        super().clean()
        try:
            self.cleaned_data['sessionId']
            self.cleaned_data['browser']
            self.cleaned_data['step']
        except KeyError as e:
            raise forms.ValidationError("sessionId, browser and step must be specified")
          
        try:
            TestSession.objects.get(sessionId=self.cleaned_data['sessionId']) 
            TestStep.objects.get(id=self.cleaned_data['step'])
        except Exception as e:
            raise forms.ValidationError("session or step not found")