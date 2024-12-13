'''
Created on 12 déc. 2024

'''
from django import forms
from django.contrib import admin
from variableServer.models import Variable, Application, TestCase

class ApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.fields['linkedApplication'].required = False
        self.fields['linkedApplication'].queryset = Application.objects.exclude(id=self.instance.id) # exclude the application itself to avoid looping
     
    class Meta:
        model = Application
        fields = ['name', 'linkedApplication']
        
    
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    form = ApplicationForm

    # deactivate all actions so that deleting an application must be done from detailed view
    actions = None
    
    def get_fieldsets(self, request, obj=None):
        """
        Display error message when it's impossible to delete the application
        """
        if not (obj and len(TestCase.objects.filter(application=obj)) and len(Variable.objects.filter(application=obj))):
            return admin.ModelAdmin.get_fieldsets(self, request, obj=obj)
        
        # if some variables are linked to this application
        else:
            return (
                 (None, {
                        'fields': ('name', 'linkedApplication'),
                        'description': '<div style="font-size: 16px;color: red;">All tests / variables must be deleted before this application can be deleted</div>'}
                  ),
                 )
               
    def has_delete_permission(self, request, obj=None):
        """
        Do not display delete button if some tests / variables are linked to this application
        """
        
        can_delete = admin.ModelAdmin.has_delete_permission(self, request, obj=obj)
        
        # when no object provided, default behavior
        if not obj:
            return can_delete
        
        # check for linked test cases and variables
        if len(TestCase.objects.filter(application=obj)) or len(Variable.objects.filter(application=obj)):
            return False
        else:
            return can_delete 
