from django.db import models

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
    
class TestEnvironment(models.Model):
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class TestCase(models.Model):
    name = models.CharField(max_length=100)
    version = models.ForeignKey(Version, related_name='testCase')
    testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True)
    
    def __str__(self):
        return "%s - %s" % (self.name, self.version.name)
    
class TestStep(models.Model):
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name 
    
class TestSession(models.Model):
    sessionId = models.CharField(max_length=32)
    date = models.DateField()
    testCases = models.ManyToManyField("TestCase", related_name='testsession', blank=True)
    browser = models.CharField(max_length=20)
    environment = models.ForeignKey(TestEnvironment, related_name='testsession')
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):
    step = models.ForeignKey(TestStep, related_name='snapshots')
    image = models.ImageField(upload_to='documents/')
    isReference = models.BooleanField(default=False)
    session = models.ForeignKey(TestSession)
    testCase = models.ForeignKey(TestCase)
    
class Difference(models.Model):
    reference = models.ForeignKey(Snapshot, related_name='differenceRef')
    compared = models.ForeignKey(Snapshot, related_name='differenceComp')
    pixels = models.BinaryField(null=True)

    
