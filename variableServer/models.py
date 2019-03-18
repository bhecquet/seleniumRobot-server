from django.db import models
import commonsServer
from commonsServer.models import TestEnvironment as TE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
import datetime
from django.utils import timezone

class TestEnvironment(commonsServer.models.TestEnvironment):
    class Meta:
        proxy = True

class Application(commonsServer.models.Application):
    class Meta:
        default_permissions = ('add', 'change', 'delete')
        proxy = True
        
class Version(commonsServer.models.Version):
    class Meta:
        proxy = True

class TestCase(commonsServer.models.TestCase):
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
    
    def save(self, *args, **kwargs):
        super(Variable, self).save(*args, **kwargs)
        self._correctReservableState()
    
    def _correctReservableState(self):
        """
        Make sure that all variable of the same scope have the same reservable state as the new/updated variable
        """
        similarVariables = Variable.objects.filter(name=self.name, application=self.application, version=self.version, environment=self.environment, test=self.test).exclude(reservable=self.reservable)
        for var in similarVariables:
            var.reservable = self.reservable
            var.save()
    
    
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=300, blank=True)
    application = models.ForeignKey(Application, null=True) 
    environment = models.ForeignKey(TestEnvironment, null=True)
    version = models.ForeignKey(Version, null=True)
    test = models.ForeignKey(TestCase, null=True)
    releaseDate = models.DateTimeField(null=True)
    reservable = models.BooleanField(default=False, help_text="tick it if this variable should be reserved when used to prevent other tests to use it at the same time. Default is false")
    internal = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)
    description = models.CharField(max_length=500, default="", null=True)
    creationDate = models.DateTimeField(default=timezone.now)
    timeToLive = models.IntegerField(default=-1, help_text="number of days this variable will live before being destroyed. If < 0, this variable will live forever")
    # When adding a field, don't forget to add it in serializers.py
    
