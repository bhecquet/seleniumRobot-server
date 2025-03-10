'''
Created on 12 déc. 2024

@author: S047432
'''
from django.template.context_processors import csrf
from django.shortcuts import render
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from variableServer.models import Variable, Application
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django import forms
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin
from variableServer.admin_site.application_admin import ApplicationFilter

class VersionFilter(SimpleListFilter):
    """
    Depending on selected application, will show only related versions
    """
    title = 'Version'
    parameter_name = 'version'

    def lookups(self, request, model_admin):
        if 'application__id__exact' in request.GET:
            app_id = request.GET['application__id__exact']
            versions = set([c.version for c in model_admin.model.objects.all().filter(application=app_id)])
        else:
            versions = set([c.version for c in model_admin.model.objects.all()])
        return [(v.id, str(v)) for v in versions if v is not None] + [('_None_', 'None')]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '_None_':
                queryset = queryset.filter(version__id__exact=None)
            else:
                queryset = queryset.filter(version__id__exact=self.value())

        return queryset
        
        
class VersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        
class VersionAdmin(BaseServerModelAdmin): 
    list_display = ('name', 'application')
    list_filter = (ApplicationFilter,)
    form = VersionForm
    
    # deactivate all actions so that deleting a version must be done from detailed view
    actions = None
    
    def get_fieldsets(self, request, obj=None):
        """
        Display error message when it's impossible to delete the version
        """
        if not (obj and len(Variable.objects.filter(version=obj))):
            return admin.ModelAdmin.get_fieldsets(self, request, obj=obj)
        
        # if some variables are linked to this application
        else:
            return (
                 (None, {
                        'fields': ('name', 'application'),
                        'description': '<div style="font-size: 16px;color: red;">This version will be deleted when all linked variables will be deleted</div>'}
                  ),
                 )
            
            
            
    def has_delete_permission(self, request, obj=None):
        """
        Do not display delete button if some tests / variables are linked to this application
        """
        
        can_delete = super().has_delete_permission(request, obj=obj)
        
        # when no object provided, default behavior
        if not obj:
            return can_delete
        
        # check for linked variables
        if len(Variable.objects.filter(version=obj)):
            return False
        else:
            return can_delete  
        
    def get_queryset(self, request):
        """
        Filter the returned versions with the application user is allowed to see
        """
        return super().get_queryset(request, 'variableServer.view_version')
        