import os

from auditlog.signals import pre_log
from django.dispatch import receiver
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save, post_delete

from auditlog.registry import auditlog

import commonsServer.models
from commonsServer.utils.encryption import encrypt_data, decrypt_data



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

class Value(str):
    pass

class EncryptedField(models.CharField):
    """
    encrypted CharField in database
    Compatible with unencrypted data, encrypted strings will be carried
    """

    def __init__(self, *args, **kwargs):
        self.prefix = "aes_str::::"
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """
        After decrypting data library
        """
        if value is None:
            return value
        if value.startswith(self.prefix):
            value = value[len(self.prefix):]
            return decrypt_data(value)
        else:
            return value

    def to_python(self, value):
        """
        Form clean and de-serialization call (when), decrypting data
        """
        if value is None:
            return value
        elif value.startswith(self.prefix):
            value = value[len(self.prefix):]
            return decrypt_data(value)
        else:
            return value

    def get_prep_value(self, value):
        """
        Before the encrypted data storage
        """
        if value and isinstance(value, Value):
            value = encrypt_data(value)
            value = self.prefix + value
        elif isinstance(value, str):
            return value
        elif value is not None and value != '':
            raise TypeError(str(value) + "is not a valid value for EncryptedField")
        return value

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

    def get_file_path(self):
        filename = self.uploadFile.name.split("/")[-1]
        if self.application:
            return os.path.join(settings.MEDIA_ROOT, 'variables', self.application.name, filename)
        else:
            return os.path.join(settings.MEDIA_ROOT, 'variables', filename)

    def delete_variable_file(self):
        try:
            file_path = self.get_file_path()
            os.remove(file_path)
        except:
            #file already deleted or corrupted
            pass

    def save(self, *args, **kwargs):
        if self.id:
            var = Variable.objects.get(id=self.id)
            if var.uploadFile != self.uploadFile:
                var.delete_variable_file()


        super().save(*args, **kwargs)
        self._correctReservableState()

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
        return os.path.join('variables', instance.application.name, filename)

    name = models.CharField(max_length=100)
    value = EncryptedField(max_length=3000, blank=True)
    uploadFile = models.FileField(blank=True, upload_to=get_upload_path)
    description = models.CharField(max_length=500, default="", null=True)
    application = models.ForeignKey(Application, null=True, on_delete=models.CASCADE) 
    environment = models.ForeignKey(TestEnvironment, null=True, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, null=True, on_delete=models.CASCADE)
    test = models.ManyToManyField(TestCase)
    releaseDate = models.DateTimeField(null=True)
    reservable = models.BooleanField(default=False, help_text="tick it if this variable should be reserved when used to prevent other tests to use it at the same time. Default is false")
    internal = models.BooleanField(default=False, help_text="tick it if this variable has been created by a selenium test. Variable of such type should be prefixed with 'custom.test.variable'")
    protected = models.BooleanField(default=False)
    creationDate = models.DateTimeField(default=timezone.now)
    timeToLive = models.IntegerField(default=-1, help_text="number of days this variable will live before being destroyed. If < 0, this variable will live forever")
    # When adding a field, don't forget to add it in serializers.py


@receiver(pre_save, sender=Variable)
def update_variable_value(sender, instance, **kwargs):
    """
    When a StepReference is deleted, remove the associated picture
    """

    if not isinstance(instance, Value) and instance.protected and instance.value is not None:
        instance.value = Value(instance.value)

@receiver(post_delete, sender=Variable)
def delete_variable_file(sender, instance, **kwargs):
    """
    When variable is deleted, remove the associated file if any
    """
    if instance.uploadFile:
        instance.delete_variable_file()

def custom_mask(value: str) -> str:
    return value[:2] + "****" + value[-1:]

auditlog.register(Variable, mask_fields=['value'], mask_callable='variableServer.models.custom_mask')