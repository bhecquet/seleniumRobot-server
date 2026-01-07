'''
Created on 12 déc. 2024

'''
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import render
from django.template.context_processors import csrf
from magic import magic

from variableServer.admin_site.application_admin import ApplicationFilter
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin, \
    is_user_authorized
from variableServer.admin_site.environment_admin import EnvironmentFilter
from variableServer.admin_site.version_admin import VersionFilter
from variableServer.models import Variable, TestCase, Version


class VariableForm(forms.ModelForm):
    
    
    class Meta:
        model = Variable
        exclude = []

    def __init__(self, *args, **kwargs):
        super(VariableForm, self).__init__(*args, **kwargs)
        
        try:
            user = self.instance.user
        except:
            user = None
        
        # required
        self.fields['application'].required = False
        self.fields['version'].required = False
        self.fields['test'].required = False
        self.fields['environment'].required = False
        self.fields['releaseDate'].required = False
        self.fields['internal'].required = False
        self.fields['protected'].required = False
        self.fields['description'].required = False
        
        # field length
        self.fields['value'].widget.attrs['style'] = "width:50em"
        self.fields['name'].widget.attrs['style'] = "width:30em"
        self.fields['description'].widget.attrs['style'] = "width:70em"

        # change value of available tests and versions depending on "application" value
        if 'application' in self.initial and self.initial['application'] != None:
            self.fields['test'].help_text = "If 'application' value is modified, click 'save and continue editing' to display the related list of tests"
            self.fields['test'].queryset = TestCase.objects.filter(application__id=self.initial['application'])
            
            self.fields['version'].help_text = "If 'application' value is modified, click 'save and continue editing' to display the related list of versions"
            self.fields['version'].queryset = Version.objects.filter(application__id=self.initial['application'])
        else:
            self.fields['test'].help_text = "Select an application, click 'save and continue editing' to display the list of related tests"
            self.fields['test'].disabled = True
            
            self.fields['version'].help_text = "Select an application, click 'save and continue editing' to display the list of related versions"
            self.fields['version'].disabled = True
        
     
        # display fields depending on connected user
        # If a variable is protected, display value only if user has right to see it through 'see_protected_var' permission
        if self.initial.get('protected', False) and not is_user_authorized(user):
            self.initial['value'] = "****"
            self.fields['protected'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        uploadFile = cleaned_data.get("uploadFile")
        value = cleaned_data.get("value")

        if uploadFile and value:
            raise forms.ValidationError("A variable can't be both a value and a file. Choose only one.")

        if uploadFile:
            uploadFileType = magic.from_buffer(uploadFile.read(), mime=True)
            uploadFile.seek(0)
            if uploadFileType not in ["text/plain","application/vnd.ms-excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                raise forms.ValidationError(uploadFileType + " is an unsupported file type. Please, select csv, xls or json file.")
            if uploadFileType == "text/plain":
                if 'uploadFile' in self.changed_data and uploadFile.content_type not in ["application/json", "text/csv"]:
                    raise forms.ValidationError(uploadFileType + " in an unsupported file type. Please, select csv, xls or json file.")
            if uploadFile.size > 1000000:
                raise forms.ValidationError("File too large. 1Mo max")

        return cleaned_data

class VariableForm2(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VariableForm2, self).__init__(*args, **kwargs)
        self.fields['application'].required = False
        self.fields['version'].required = False
        self.fields['test'].required = False
        self.fields['environment'].required = False
        self.fields['reservable'].required = False
        
    def get_initial_for_field(self, field, field_name):
        """
        Method taking ManyToManyFields into account. Otherwise, we get a KeyError when modifying a variable
        """
        if field_name == 'test':
            initial_value = self.initial.get(field_name, field.initial)
            if initial_value:
                return initial_value.all()
            else:
                return None
        else:
            return super(VariableForm2, self).get_initial_for_field(field, field_name)

    class Meta:
        model = Variable
        fields = ['application', 'version', 'environment', 'test', 'reservable']
    

    
class VariableAdmin(BaseServerModelAdmin): 
    list_display = ('nameWithApp', 'value', 'uploadFileReforged', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate')
    list_display_protected = ('nameWithApp', 'valueProtected', 'uploadFileReforged', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate')
    list_filter = (ApplicationFilter, VersionFilter, EnvironmentFilter, 'internal')
    search_fields = ['name', 'value']
    form = VariableForm
    actions = ['delete_selected', 'copy_to', 'change_values_at_once', 'unreserve_variable']
    
    def get_list_display(self, request):
        if is_user_authorized(request.user):
            return self.list_display
        else:
            return self.list_display_protected
        
    def get_queryset(self, request):
        """
        Filter the returned variables with the application user is allowed to see
        """
        return super().get_queryset(request, 'variableServer.view_variable')

    def save_model(self, request, obj, form, change):
        """
        In case user is not allowed to see protected vars (and modifying them), this method will restore default values
        """
        
        user = request.user
        
        # before saving, get the 'protected' flag from database
        try:
            db_obj = Variable.objects.get(id=obj.id)
    
            # In case user is not allowed to see value, he will not modify it
            if db_obj.protected and not is_user_authorized(user):
                obj.protected = db_obj.protected
                obj.value = db_obj.value
        except:
            # In case of adding variable, it's not already present in database, so continue
            pass
        
        admin.ModelAdmin.save_model(self, request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """
        redefine method so that user can be used in requests
        """
        try:
            obj.user = request.user
        except:
            pass

        return admin.ModelAdmin.get_form(self, request, obj=obj, **kwargs)
    
    def _get_default_values(self, selected_variables):
        """
        Render default values as dict depending of variables to modify
        """
            
        if not selected_variables:
            return {'environment': None,
                     'application': None,
                     'test': None,
                     'version': None,
                     'reservable': False
                     }
        else:
            ref_variable = Variable.objects.get(id=int(selected_variables[0]))
    
        default_values = {'environment': ref_variable.environment,
                         'application': ref_variable.application,
                         'test': ref_variable.test,
                         'version': ref_variable.version,
                         'reservable': ref_variable.reservable
                         }
        
        for variable_id in selected_variables[1:]:
            variable = Variable.objects.get(id=int(variable_id))
            if variable.environment != ref_variable.environment:
                default_values['environment'] = None
            if variable.application != ref_variable.application:
                default_values['application'] = None
            # take ManyToMany relationship for test into account
            if not (variable.test and ref_variable.test) or list(variable.test.all()) != list(ref_variable.test.all()):
                default_values['test'] = None
            if variable.version != ref_variable.version:
                default_values['version'] = None
            if variable.reservable != ref_variable.reservable:
                default_values['reservable'] = False
            
        return default_values
    
    def copy_to(self, request, queryset):
        """
        Action allowing to copy several variables at once
        Take common values of variables to show them to user
        """
        
        queryset = Variable.objects.filter(id__in=request.POST.getlist(ACTION_CHECKBOX_NAME))
        queryset = self._filter_variables(request, queryset, 'variableServer.add_variable', 'copy')
        
        selected = [str(var.id) for var in queryset]
        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._get_default_values(selected)),
                'queryString': request.META['QUERY_STRING']} # Allow to go back to filtered list
        args.update(csrf(request))

        return render(request, "variableServer/admin/copyTo.html", args)
    copy_to.short_description = 'copy variables'
    
    def change_values_at_once(self, request, queryset):
        """
        Action allowing to change multiple variables at once
        Take common values for all variables so that they are shown to user
        """
        queryset = Variable.objects.filter(id__in=request.POST.getlist(ACTION_CHECKBOX_NAME))
        queryset = self._filter_variables(request, queryset, 'variableServer.change_variable', 'change')
        
        selected = [str(var.id) for var in queryset]
        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._get_default_values(selected)),
                'queryString': request.META['QUERY_STRING']} # Allow to go back to filtered list
        args.update(csrf(request))

        return render(request, "variableServer/admin/changeTo.html", args)
    change_values_at_once.short_description = 'change variables'
    
    def delete_selected(self, request, queryset):
        """
        Same name as the method we override as we use it. Else django complains about an action that does not exists
        """

        queryset = self._filter_variables(request, queryset, 'variableServer.delete_variable', 'delete')
      
        return django_delete_selected(self, request, queryset)
    delete_selected.short_description = 'delete variables'
    
    def unreserve_variable(self, request, queryset):
        """
        Allow to unreserve variables (remove releaseDate)
        """
        queryset = Variable.objects.filter(id__in=request.POST.getlist(ACTION_CHECKBOX_NAME))
        queryset = self._filter_variables(request, queryset, 'variableServer.change_variable', 'unreserve')

        for variable in queryset:
            try:
                variable.releaseDate = None
                variable.save()
            except Exception as e:
                pass
    unreserve_variable.short_description = 'unreserve variables'
    
    def _filter_variables(self, request, queryset, global_permission_code_name, message):
        """
        Filters the queryset variable depending on permissions
        """
        queryset, forbidden_applications = self._filter_queryset(request, queryset, global_permission_code_name)
        
        for application in forbidden_applications:
            self.message_user(request, "You do not have right to %s variables from application %s" % (message, application), level=messages.ERROR)

        return queryset
    
