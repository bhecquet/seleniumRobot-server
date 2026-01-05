import os

from django.conf import settings
from django.db import models
from django.utils import timezone

import commonsServer.models


class TestEnvironment(commonsServer.models.TestEnvironment):
    class Meta:
        proxy = True

class Application(commonsServer.models.Application):
    class Meta:
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

    def uploadFileReforged(self):
        if "/" in str(self.uploadFile):
            return str(self.uploadFile).split("/")[-1]
        else:
            return str(self.uploadFile)
    uploadFileReforged.short_description = "uploadFile"

    def save(self, *args, **kwargs):
        if self.id:
            var = Variable.objects.get(id=self.id)
            if var.uploadFile != self.uploadFile:
                try:
                    filename = var.uploadFile.name.split("/")[-1]
                    if var.application:
                        file_path = os.path.join(settings.MEDIA_ROOT, var.application.name, filename)
                    else:
                        file_path = os.path.join(settings.MEDIA_ROOT, filename)
                    os.remove(file_path)
                except:
                    #file already deleted or corrupted
                    pass
        super(Variable, self).save(*args, **kwargs)
        self._correctReservableState()

    def delete(self, using=None, keep_parents=False):
        if self.uploadFile:
            try:
                filename = self.uploadFile.name.split("/")[-1]
                if self.application:
                    file_path = os.path.join(settings.MEDIA_ROOT, self.application.name, filename)
                else:
                    file_path = os.path.join(settings.MEDIA_ROOT, filename)
                os.remove(file_path)
            except:
                #file already deleted or corrupted ?
                pass
        super(Variable, self).delete(using, keep_parents)

    def _correctReservableState(self):
        """
        Make sure that all variable of the same scope have the same reservable state as the new/updated variable
        """
        # search all variables of the same name / application / version / environment where reservable state is not the same to update it
        similarVariables = Variable.objects.filter(name=self.name, application=self.application, version=self.version, environment=self.environment).exclude(reservable=self.reservable)
        for var in similarVariables:
            
            # tests must be the same for both variables so that variables really have the same scope
            if list(var.test.all()) == list(self.test.all()):
                var.reservable = self.reservable
                var.save()
    
    def allTests(self):
        return ",".join([t.name for t in self.test.all()])

    def get_upload_path(instance, filename):
        if not instance.application:
            return filename
        return os.path.join(instance.application.name,filename)

    name = models.CharField(max_length=100)
    value = models.CharField(max_length=3000, blank=True)
    uploadFile = models.FileField(blank=True, upload_to=get_upload_path)
    application = models.ForeignKey(Application, null=True, on_delete=models.CASCADE) 
    environment = models.ForeignKey(TestEnvironment, null=True, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, null=True, on_delete=models.CASCADE)
    test = models.ManyToManyField(TestCase)
    releaseDate = models.DateTimeField(null=True)
    reservable = models.BooleanField(default=False, help_text="tick it if this variable should be reserved when used to prevent other tests to use it at the same time. Default is false")
    internal = models.BooleanField(default=False, help_text="tick it if this variable has been created by a selenium test. Variable of such type should be prefixed with 'custom.test.variable'")
    protected = models.BooleanField(default=False)
    description = models.CharField(max_length=500, default="", null=True)
    creationDate = models.DateTimeField(default=timezone.now)
    timeToLive = models.IntegerField(default=-1, help_text="number of days this variable will live before being destroyed. If < 0, this variable will live forever")
    # When adding a field, don't forget to add it in serializers.py
    
