from django.db import models
from snapshotServer.models import TestCase
import snapshotServer

class TestEnvironment(snapshotServer.models.TestEnvironment):
    class Meta:
        proxy = True

class Application(snapshotServer.models.Application):
    class Meta:
        proxy = True

class Version(snapshotServer.models.Version):
    class Meta:
        proxy = True

class TestCase(snapshotServer.models.TestCase):
    class Meta:
        proxy = True

class Variable(models.Model):
    
    class Meta:
        permissions = (("see_protected_var", "Can see protected vars"),
                       )
    
    def __str__(self):
        return self.name
    
    def nameWithApp(self):
        if self.application:
            return "%s.%s" % (self.application, self.name)
        else:
            return self.name
    nameWithApp.short_description = 'Name'
    
    def valueProtected(self):
        """
        Return value if variable is not protected
        """
        if self.protected:
            return '****'
        else:
            return self.value
    valueProtected.short_description = 'Value'
    
    
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=300)
    application = models.ForeignKey(Application, null=True) 
    environment = models.ForeignKey(TestEnvironment, null=True)
    version = models.ForeignKey(Version, null=True)
    test = models.ForeignKey(TestCase, null=True)
    releaseDate = models.DateTimeField(null=True)
    internal = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)
    description = models.CharField(max_length=500, default="", null=True)