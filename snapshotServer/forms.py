from django import forms

from snapshotServer.models import StepResult


class ImageUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    stepResult = forms.IntegerField()
    name = forms.CharField()
    compare = forms.CharField()
    diffTolerance = forms.FloatField(required=False, max_value=100, min_value=0)
    
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
        
        if self.cleaned_data['diffTolerance'] == None:
            self.cleaned_data['diffTolerance'] = 0.0
        
        if self.cleaned_data['compare'] not in ['true', 'false']:
            self.cleaned_data['compare'] = 'true'