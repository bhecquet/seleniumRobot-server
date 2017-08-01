from django import forms

from snapshotServer.models import TestSession, TestStep, TestCaseInSession


class ImageUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    stepResult = forms.IntegerField()
    testCase = forms.IntegerField()
    sessionId = forms.CharField()
    
    def clean(self):
        super().clean()
        try:
            self.cleaned_data['sessionId']
            self.cleaned_data['testCase']
            self.cleaned_data['stepResult']
        except KeyError as e:
            raise forms.ValidationError("sessionId, testCase and stepResult must be specified")
          
        try:
            TestSession.objects.get(sessionId=self.cleaned_data['sessionId']) 
            TestStep.objects.get(id=self.cleaned_data['stepResult'])
            TestCaseInSession.objects.get(id=self.cleaned_data['testCase'])
        except Exception as e:
            raise forms.ValidationError("session, testCase or stepResult not found")