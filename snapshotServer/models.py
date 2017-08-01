from distutils.version import LooseVersion

from django.db import models

from snapshotServer.controllers.PictureComparator import Rectangle
import pickle


# Create your models here.
class Application(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Version(models.Model):
    application = models.ForeignKey(Application, related_name='version')
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.application.name + '-' + self.name
    
    def previousVersions(self):
        """
        Get all versions for the same application, previous to this one
        """
        versions = [v for v in Version.objects.filter(application=self.application) if LooseVersion(v.name) < LooseVersion(self.name)]
        versions.sort(key=lambda v: LooseVersion(v.name), reverse=False)
        return versions
    
    def nextVersions(self):
        """
        Get all versions for the same application, previous to this one
        """
        versions = [v for v in Version.objects.filter(application=self.application) if LooseVersion(v.name) >= LooseVersion(self.name)]
        versions.sort(key=lambda v: LooseVersion(v.name), reverse=False)
        return versions
    
class TestEnvironment(models.Model):
    """
    An environment can be linked to an other one
    For example, NonReg1 is a NonReg environment from which it will get all variables
    """
    
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
    genericEnvironment = models.ForeignKey('self', null=True)
    genericEnvironment.short_description = 'generic environnement'

class TestCase(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100)
    application = models.ForeignKey(Application, related_name='testCase')
    
    def __str__(self):
        return "%s - %s" % (self.name, self.application.name)
    
    
class TestCaseInSession(models.Model):
    """
    The test case in a test session
    """
    __test__= False  # avoid detecting it as a test class
    testCase = models.ForeignKey(TestCase, related_name="testCaseInSession")
    session = models.ForeignKey('TestSession')
    testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True)
    stacktrace = models.TextField(null=True)
    
    def isOkWithSnapshots(self):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the snapshot should
        show a diff
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        result = True 
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            pixels = pickle.loads(snapshot.pixelsDiff)
            
            result = result and not bool(pixels)
            
        return result
    
    def isOkWithResult(self):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the steps should be KO (look at StepResult object)
        """
        
        stepResults = StepResult.objects.filter(testCase=self)

        for stepResult in stepResults:
            if not stepResult.result:
                return False
            
        return True
    
    def __str__(self):
        return "%s - %s" % (self.testCase.name, self.session.version.name)
    
class TestStep(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name 
    
    
    def isOkWithSnapshots(self, testSessionId, testCaseId):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the snapshot should
        show a diff
        @param testSessionId: testSessionId
        @param testCaseIdparam: the test case this step belongs
        """
        
        snapshots = Snapshot.objects.filter(session=testSessionId, testCase=testCaseId, step=self)
        result = True 
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            pixels = pickle.loads(snapshot.pixelsDiff)
            
            result = result and not bool(pixels)
            
        return result
    
class TestSession(models.Model):
    __test__= False  # avoid detecting it as a test class
    sessionId = models.CharField(max_length=50)
    date = models.DateField()
    version = models.ForeignKey(Version, related_name='testsession')
    browser = models.CharField(max_length=20)
    environment = models.ForeignKey(TestEnvironment, related_name='testsession')
    
    def __str__(self):
        return "Session %s with %s" % (self.sessionId, self.browser)
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):
#     step = models.ForeignKey(TestStep, related_name='snapshots')
#     image = models.ImageField(upload_to='documents/')
#     session = models.ForeignKey(TestSession)
#     testCase = models.ForeignKey(TestCaseInSession)
#     refSnapshot = models.ForeignKey('self', default=None, null=True)
#     pixelsDiff = models.BinaryField(null=True)
#     tooManyDiffs = models.BooleanField(default=False)
    stepResult = models.ForeignKey('StepResult', related_name='snapshots')
    image = models.ImageField(upload_to='documents/')
    refSnapshot = models.ForeignKey('self', default=None, null=True)
    pixelsDiff = models.BinaryField(null=True)
    tooManyDiffs = models.BooleanField(default=False)
    
    def __str__(self):
        return "%s - %s - %s - %d" % (self.stepResult.testCase.testCase.name, self.stepResult.step.name, self.session.sessionId, self.id) 
    
    def snapshotsUntilNextRef(self, refSnapshot):
        """
        get all snapshots, sharing the same reference snapshot, until the next reference for the same testCase / testStep
        """
        nextSnapshots = Snapshot.objects.filter(stepResult__step=self.stepResult.step, 
                                            stepResult__testCase__testCase__name=self.stepResult.testCase.testCase.name, 
                                            stepResult__testCase__session__version__in=self.stepResult.testCase.session.version.nextVersions(),
                                            refSnapshot=refSnapshot,
                                            id__gt=self.id) \
                                        .order_by('id')
        
        snapshots = []
        
        for snap in nextSnapshots:
            if snap.refSnapshot:
                snapshots.append(snap)
            else:
                break
        
        return snapshots
    
    def snapshotWithSameRef(self):
        """
        Returns the list of snapshots sharing the same reference
        """
        if not self.refSnapshot:
            return []
        
        snapshots = Snapshot.objects.filter(stepResult__step=self.stepResult.step, 
                                            stepResult__testCase__testCase__name=self.stepResult.testCase.testCase.name, 
                                            refSnapshot=self.refSnapshot) \
                                        .order_by('id')
                          
        newSnapshots = []              
        for snap in snapshots:
            if snap != self:
                newSnapshots.append(snap)
                
        return newSnapshots
        
class StepResult(models.Model):
    step = models.ForeignKey(TestStep, related_name='stepresult')
    testCase = models.ForeignKey(TestCaseInSession, related_name='stepresult')
    result = models.BooleanField(null=False)
    stacktrace = models.TextField(null=True)
    
class ExcludeZone(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    snapshot = models.ForeignKey(Snapshot)
    
    def __str__(self):
        return "(x, y, width, height) = (%d, %d, %d, %d)" % (self.x, self.y, self.width, self.height)
    
    def toRectangle(self):
        return Rectangle(self.x, self.y, self.width, self.height)
    
