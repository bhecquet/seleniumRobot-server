from __future__ import unicode_literals, absolute_import, division
'''
Created on 8 dec. 2017

@author: S047432
'''
from commonsServer.models import Application
import variableServer
import snapshotServer

"""Add permissions for proxy model.
This is needed because of the bug https://code.djangoproject.com/ticket/11154
in Django (as of 1.6, it's not fixed).
When a permission is created for a proxy model, it actually creates if for it's
base model app_label (eg: for "article" instead of "about", for the About proxy
model).
What we need, however, is that the permission be created for the proxy model
itself, in order to have the proper entries displayed in the admin.
"""



import sys

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import Q

class Command(BaseCommand):
    help = "Fix permissions for proxy models."

    def handle(self, *args, **options):
        for model in apps.get_models():
            opts = model._meta
            ctype, created = ContentType.objects.get_or_create(
                app_label=opts.app_label,
                model=opts.object_name.lower())

            for codename, name in _get_all_permissions(opts):
                p, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=ctype,
                    defaults={'name': name})
                if created:
                    sys.stdout.write('Adding permission {}\n'.format(p))

        # add application specific rights
        for app in Application.objects.all():
            content_type = ContentType.objects.get_for_model(Application)
            Permission.objects.get_or_create(
                codename=Application.appPermissionCode + app.name,
                name='Can view application and related variables and versions for ' + app.name,
                content_type=content_type,
                )
            
        # add 'Variable Users' group
        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')
        
        # Add permissions to 'Variable Users' group
        ct = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_application') | Q(codename='change_application') , content_type=ct))
        ct = ContentType.objects.get_for_model(variableServer.models.TestCase, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_testcase') | Q(codename='change_testcase') , content_type=ct))
        ct = ContentType.objects.get_for_model(variableServer.models.TestEnvironment, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_testenvironment') | Q(codename='change_testenvironment') , content_type=ct))
        ct = ContentType.objects.get_for_model(variableServer.models.Version, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_version') | Q(codename='change_version') , content_type=ct))
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable') | Q(codename='delete_variable') | Q(codename='see_protected_var') , content_type=ct))
        
            
        # add 'Variable Users' group
        snapshot_users_group, created = Group.objects.get_or_create(name='Snapshot Users')
        
        # Add permissions to 'Snapshot Users' group
        ct = ContentType.objects.get_for_model(snapshotServer.models.ExcludeZone)
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_excludezone') | Q(codename='change_excludezone') | Q(codename='delete_excludezone') , content_type=ct))
        ct = ContentType.objects.get_for_model(snapshotServer.models.Snapshot) # for upload
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_snapshot') | Q(codename='change_snapshot') , content_type=ct))
        ct = ContentType.objects.get_for_model(snapshotServer.models.TestCaseInSession)
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_testcaseinsession') | Q(codename='change_testcaseinsession') , content_type=ct))
        ct = ContentType.objects.get_for_model(snapshotServer.models.StepResult)
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_stepresult') | Q(codename='change_stepresult') , content_type=ct))
        ct = ContentType.objects.get_for_model(snapshotServer.models.TestSession)
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_testsession') | Q(codename='change_testsession') , content_type=ct))
        ct = ContentType.objects.get_for_model(snapshotServer.models.TestStep)
        snapshot_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_teststep') | Q(codename='change_teststep') , content_type=ct))

        print("Groups and permissions added")
        
        
        
        
        
        