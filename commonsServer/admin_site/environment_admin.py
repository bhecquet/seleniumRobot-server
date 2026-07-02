'''
Created on 12 déc. 2024

'''
from operator import attrgetter

from django import forms
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

from seleniumRobotServer.permissions.permissions import ContextPermissionChecker
from commonsServer.admin_site.base_model_admin import bypass_context_permissions
from variableServer.models import TestEnvironment

class EnvironmentFilter(SimpleListFilter):
    """
    Depending on selected application, will show only related environments
    """
    title = 'Environment'
    parameter_name = 'environment'

    def lookups(self, request, model_admin):
        if bypass_context_permissions(request, 'variableServer.view_testenvironment'):
            return [(e.id, str(e)) for e in TestEnvironment.objects.all().order_by('name')] + [('_None_', 'None')]

        allowed_applications = ContextPermissionChecker.get_allowed_applications(request)
        allowed_environments = ContextPermissionChecker.get_allowed_environments(request)

        if 'application' in request.GET:
            app_id = request.GET['application']
            environments = {c.environment for c in model_admin.model.objects.all().filter(application=app_id)}
        else:
            environments = set(TestEnvironment.objects.all().order_by('name'))

        environments = [e for e in environments if e is not None]

        # in case user has no permission on application, it will only see environments on which he has permissions for
        if not allowed_applications:
            environments = [e for e in environments if e.name in allowed_environments]

        environments = sorted(environments, key=attrgetter('name'))
        return [(e.id, str(e)) for e in environments] + [('_None_', 'None')]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '_None_':
                return queryset.filter(environment__id=None)
            else:
                return queryset.filter(environment__id=self.value())
        else:
            return queryset

class EnvironmentForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(EnvironmentForm, self).__init__(*args, **kwargs)
        self.fields['genericEnvironment'].required = False
   
class EnvironmentAdmin(admin.ModelAdmin):
    list_filter = ('genericEnvironment', )
    list_display = ('name', 'genericEnvironment')
    actions = ['delete_selected']
    form = EnvironmentForm
    