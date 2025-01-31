from django import forms

from snapshotServer.models import StepResult, Version, TestEnvironment,\
    Application, TestCase, TestSession, TestStep, TestCaseInSession, ExcludeZone
import datetime


class ImageForComparisonUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField()
    stepResult = forms.IntegerField()
    name = forms.CharField()
    compare = forms.CharField()
    diffTolerance = forms.FloatField(required=False, max_value=100, min_value=0)
    excludeZones = forms.JSONField(required=False)
    
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

        if self.cleaned_data['excludeZones'] == None:
            self.cleaned_data['excludeZones'] = []
        else:
            self.cleaned_data['excludeZones'] = [ExcludeZone(x=e['x'], y=e['y'], width=e['width'], height=e['height']) for e in self.cleaned_data['excludeZones']]
        
        
        self.cleaned_data['storeSnapshot'] = True
        
        if self.cleaned_data['diffTolerance'] == None:
            self.cleaned_data['diffTolerance'] = 0.0
        
        if self.cleaned_data['compare'] not in ['true', 'false']:
            self.cleaned_data['compare'] = 'true'
            
class ImageForComparisonUploadFormNoStorage(forms.Form):
    """
    Image upload form.
    This form will create a temp StepResult so that we can compare the image with reference
    without recording every test session details
    """
    image = forms.ImageField()
    stepName = forms.CharField()
    testCaseName = forms.CharField()
    versionId = forms.CharField()
    environmentId = forms.CharField()
    browser = forms.CharField()
    name = forms.CharField()
    compare = forms.CharField()
    diffTolerance = forms.FloatField(required=False, max_value=100, min_value=0)
    excludeZones = forms.JSONField(required=False)
    
    def clean(self):
        super().clean()
        try:
            self.cleaned_data['stepName']
            self.cleaned_data['testCaseName']
            self.cleaned_data['versionId']
            self.cleaned_data['environmentId']
            self.cleaned_data['browser']
        except KeyError as e:
            raise forms.ValidationError("stepName, testCaseName, version, environment, browser must be specified")
          
          
        # create the StepResult object from provided data
        version = Version.objects.get(id=self.cleaned_data['versionId'])
        environment = TestEnvironment.objects.get(id=self.cleaned_data['environmentId'])
        test_case = TestCase(name=self.cleaned_data['testCaseName'], 
                            application=version.application)
        test_session = TestSession(sessionId='123',
                                  version=version,
                                  browser=self.cleaned_data['browser'],
                                  environment=environment,
                                  compareSnapshot=True,
                                  ttl=datetime.timedelta(days=0))
        
        step = TestStep.objects.get(name=self.cleaned_data['stepName'])
        test_case_in_session = TestCaseInSession(testCase=test_case, 
                                              session=test_session
                                              )
        self.cleaned_data['stepResult'] = StepResult(step=step, 
                                 testCase=test_case_in_session,
                                 result=True)
        self.cleaned_data['storeSnapshot'] = False
        
        if self.cleaned_data['excludeZones'] == None:
            self.cleaned_data['excludeZones'] = []
        else:
            self.cleaned_data['excludeZones'] = [ExcludeZone(x=e['x'], y=e['y'], width=e['width'], height=e['height']) for e in self.cleaned_data['excludeZones']]
        
        if self.cleaned_data['diffTolerance'] == None:
            self.cleaned_data['diffTolerance'] = 0.0
        
        # TODO: handle other cases
        if self.cleaned_data['compare'] not in ['true', 'false']:
            self.cleaned_data['compare'] = 'true'

class ImageForStepReferenceUploadForm(forms.Form):
    """Image upload form."""
    image = forms.FileField()
    stepResult = forms.IntegerField()
    
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


class ImageForFieldDetectionForm(forms.Form):
    """
    Image upload form for field detection
    - task represent the type of detection we will use.
    """
    image = forms.FileField()
    task = forms.CharField()
    resizeFactor = forms.FloatField(required=False)

    def clean(self):
        super().clean()
        try:
            if self.cleaned_data['task'] not in ['error', 'field']:
                raise KeyError("")
        except KeyError as e:
            raise forms.ValidationError("task must be specified ('error' or 'field')")

        if self.cleaned_data['resizeFactor'] == None:
            self.cleaned_data['resizeFactor'] = 1.0


class DataForFieldDetectionForm(forms.Form):
    """
    Image upload form for field detection
    - task represent the type of detection we will use.
    """

    image = forms.CharField(required=False)
    stepResultId = forms.CharField(required=False)
    version = forms.CharField(required=False)
    output = forms.CharField()

    def clean(self):
        super().clean()
        
        # image may not be provided
        self.cleaned_data['image'] = self.cleaned_data.get('image')
        self.cleaned_data['stepResultId'] = self.cleaned_data.get('stepResultId')
        self.cleaned_data['version'] = self.cleaned_data.get('version')
        
        if self.cleaned_data.get('output') not in ['json', 'image']:
            raise forms.ValidationError("'output' must be specified ('json' or 'image')")
        
        if not (self.cleaned_data['stepResultId'] or self.cleaned_data['image']):
            raise forms.ValidationError("'image' OR 'stepResultId' parameters are mandatory")

