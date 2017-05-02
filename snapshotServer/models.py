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
    environment = models.ForeignKey(TestEnvironment, related_name='testCases', on_delete=models.CASCADE)
    version = models.ForeignKey(Version, related_name='testCases', on_delete=models.CASCADE)
    
    def __str__(self):
        return "%s - %s - %s" % (self.name, self.environment.name, self.version.name)
    
class TestStep(models.Model):
    name = models.CharField(max_length=100)  
    testCase = models.ForeignKey(TestCase, related_name='teststep', on_delete=models.CASCADE, default=None)
    
class TestSession(models.Model):
    sessionId = models.CharField(max_length=32)
    date = models.DateField()
    testCase = models.ForeignKey(TestCase, related_name='testsession')
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):
    step = models.ForeignKey(TestStep, related_name='snapshots', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='documents/', default=None)
    browser = models.CharField(max_length=20)
    isReference = models.BooleanField(default=False)
    session = models.ForeignKey(TestSession, default=None)
    
class Difference(models.Model):
    reference = models.ForeignKey(Snapshot, related_name='differenceRef')
    compared = models.ForeignKey(Snapshot, related_name='differenceComp')
    pixels = models.BinaryField(null=True)
    
