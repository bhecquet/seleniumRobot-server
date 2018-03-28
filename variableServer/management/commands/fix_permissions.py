from __future__ import unicode_literals, absolute_import, division
'''
Created on 8 dec. 2017

@author: S047432
'''
from commonsServer.models import Application

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
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.apps import apps

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