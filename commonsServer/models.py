from django.db import models
from distutils.version import LooseVersion

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