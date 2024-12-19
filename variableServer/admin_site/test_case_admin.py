from django import forms
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin
from django.conf import settings
from variableServer.models import Application
from variableServer.admin_site.application_admin import ApplicationFilter



class TestCaseForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(TestCaseForm, self).__init__(*args, **kwargs)

class TestCaseAdmin(BaseServerModelAdmin): 
    list_display = ('name', 'application')
    list_filter = (ApplicationFilter,)
    form = TestCaseForm
    actions = ['delete_selected']

    def get_queryset(self, request):
        """
        Filter the returned versions with the application user is allowed to see
        """
        qs = super(TestCaseAdmin, self).get_queryset(request)
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or request.user.has_perm('variableServer.view_testcase'):
            return qs
         
        for application in Application.objects.all():
            if not request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + application.name):
                qs = qs.exclude(application__name=application.name)
                
        if not request.user.has_perm('variableServer.view_testcase'):
            qs = qs.exclude(application=None)
                 
        return qs  