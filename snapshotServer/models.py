from django.db import models
from distutils.version import LooseVersion

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
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class TestCase(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100)
    version = models.ForeignKey(Version, related_name='testCase')
    testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True)
    
    def __str__(self):
        return "%s - %s" % (self.name, self.version.name)
    
class TestStep(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name 
    
class TestSession(models.Model):
    __test__= False  # avoid detecting it as a test class
    sessionId = models.CharField(max_length=32)
    date = models.DateField()
    testCases = models.ManyToManyField("TestCase", related_name='testsession', blank=True)
    browser = models.CharField(max_length=20)
    environment = models.ForeignKey(TestEnvironment, related_name='testsession')
    
    def __str__(self):
        
        return "Session %s testing %s with %s" % (self.sessionId, str([t.name for t in self.testCases.all()]), self.browser)
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):
    step = models.ForeignKey(TestStep, related_name='snapshots')
    image = models.ImageField(upload_to='documents/')
    session = models.ForeignKey(TestSession)
    testCase = models.ForeignKey(TestCase)
    refSnapshot = models.ForeignKey('self', default=None, null=True)
    pixelsDiff = models.BinaryField(null=True)
    
    def __str__(self):
        return "%s - %s - %s - %d" % (self.testCase.name, self.step.name, self.session.sessionId, self.id) 
    
    def snapshotsUntilNextRef(self, refSnapshot):
        """
        get all snapshot until the next reference for the same testCase / testStep
        Filter by the same reference snapshot
        """
        nextSnapshots = Snapshot.objects.filter(step=self.step, 
                                            testCase__name=self.testCase.name, 
                                            testCase__version__in=self.testCase.version.nextVersions(),
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
    

    
