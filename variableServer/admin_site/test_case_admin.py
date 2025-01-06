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
        return super().get_queryset(request, 'variableServer.view_testcase')
