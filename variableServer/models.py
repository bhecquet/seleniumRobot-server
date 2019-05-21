from django.db import models
import commonsServer
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
        similarVariables = Variable.objects.filter(name=self.name, application=self.application, version=self.version, environment=self.environment).exclude(reservable=self.reservable)
        for var in similarVariables:
            if list(var.test.all()) == list(self.test.all()):
                var.reservable = self.reservable
                var.save()
    
    def allTests(self):
        return ",".join([t.name for t in self.test.all()])
    
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=300, blank=True)
    application = models.ForeignKey(Application, null=True, on_delete=models.CASCADE) 
    environment = models.ForeignKey(TestEnvironment, null=True, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, null=True, on_delete=models.CASCADE)
    test = models.ManyToManyField(TestCase)
    releaseDate = models.DateTimeField(null=True)
    reservable = models.BooleanField(default=False, help_text="tick it if this variable should be reserved when used to prevent other tests to use it at the same time. Default is false")
    internal = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)
    description = models.CharField(max_length=500, default="", null=True)
    creationDate = models.DateTimeField(default=timezone.now)
    timeToLive = models.IntegerField(default=-1, help_text="number of days this variable will live before being destroyed. If < 0, this variable will live forever")
    # When adding a field, don't forget to add it in serializers.py
    
