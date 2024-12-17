from distutils.version import LooseVersion

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import Permission


class TruncatingCharField(models.CharField):
    def get_prep_value(self, value):
        value = super(TruncatingCharField,self).get_prep_value(value)
        if value:
            return value[:self.max_length]
        return value

class Application(models.Model):
    
    appPermissionCode = 'can_view_application_'

    name = models.CharField(max_length=50)
    
    
    def get_linked_applications(self):
        linked_applications = []
        if self.linkedApplication and self.linkedApplication.id != self.id:
            linked_applications.append(self.linkedApplication)
            linked_applications += self.linkedApplication.get_linked_applications()
            
        return linked_applications
    
    linkedApplication = models.ManyToManyField("self", related_name='linked_application', symmetrical=False)
    linkedApplication.short_description = 'linked application'
    
    def __str__(self):
        return self.name
     
    def save(self, *args, **kwargs):
        super(Application, self).save(*args, **kwargs)
        content_type = ContentType.objects.get_for_model(type(self), for_concrete_model=False)
        Permission.objects.get_or_create(
            codename=Application.appPermissionCode + self.name,
            name='Can view application and related variables and versions for ' + self.name,
            content_type=content_type,
            )
        
    def delete(self, *args, **kwargs):
        super(Application, self).delete(*args, **kwargs)
        Permission.objects.get(codename=Application.appPermissionCode + self.name).delete()
    
class Version(models.Model):
    application = models.ForeignKey(Application, related_name='version', on_delete=models.CASCADE)
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
    
    def get_parent_environments(self):
        parent_environments = []
        if self.genericEnvironment and self.genericEnvironment.id != self.id:
            parent_environments.append(self.genericEnvironment)
            parent_environments += self.genericEnvironment.get_parent_environments()
            
        return parent_environments
    
    genericEnvironment = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
    genericEnvironment.short_description = 'generic environnement'

class TestCase(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=150)
    application = models.ForeignKey(Application, related_name='testCase', on_delete=models.CASCADE)
    
    def __str__(self):
        return "%s - %s" % (self.name, self.application.name)