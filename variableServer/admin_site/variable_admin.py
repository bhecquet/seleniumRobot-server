'''
Created on 12 déc. 2024

'''
from django import forms
from variableServer.models import Variable, TestCase, Version, Application
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin,\
    is_user_authorized
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import render
from django.template.context_processors import csrf
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from variableServer.admin_site.version_admin import VersionFilter
from variableServer.admin_site.environment_admin import EnvironmentFilter
from django.contrib.admin.actions import delete_selected as django_delete_selected


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
        Methode permettant de prendre en charge le ManyToManyFields. Sinon, on avait une KeyError lors de la modification d'une variable
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
    list_display = ('nameWithApp', 'value', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate')
    list_display_protected = ('nameWithApp', 'valueProtected', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate')
    list_filter = ('application', VersionFilter, EnvironmentFilter, 'internal')
    search_fields = ['name', 'value']
    form = VariableForm
    actions = ['delete_selected', 'copyTo', 'changeValuesAtOnce', 'unreserveVariable']
    
    def get_list_display(self, request):
        if is_user_authorized(request.user):
            return self.list_display
        else:
            return self.list_display_protected
        
    def get_queryset(self, request):
        """
        Filter the returned variables with the application user is allowed to see
        """
        qs = super(VariableAdmin, self).get_queryset(request)
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return qs
         
        for application in Application.objects.all():
            if not (request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + application.name) or request.user.has_perm('variableServer.view_variable')):
                qs = qs.exclude(application__name=application.name)
                
        if not request.user.has_perm('variableServer.view_variable'):
            qs = qs.exclude(application=None)
    
        return qs

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
    
    def copyTo(self, request, queryset):
        """
        Action permettant de copier plusieurs variables d'un coup
        On reprend les valeurs communes des variables pour les proposer au moment de l'écran de saisie
        """
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)

        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._get_default_values(selected)),
                'queryString': request.META['QUERY_STRING']} # permettra de revenir à la liste des variables filtrée
        args.update(csrf(request))

        return render(request, "variableServer/admin/copyTo.html", args)
    copyTo.short_description = 'copier les variables'
    
    def changeValuesAtOnce(self, request, queryset):
        """
        Action permettant de modifier plusieurs variables d'un coup
        On reprend les valeurs communes des variables pour les proposer au moment de l'écran de saisie
        """
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._get_default_values(selected)),
                'queryString': request.META['QUERY_STRING']} # permettra de revenir à la liste des variables filtrée
        args.update(csrf(request))

        return render(request, "variableServer/admin/changeTo.html", args)
    changeValuesAtOnce.short_description = 'modifier les variables'
    
    def delete_selected(self, request, queryset):
        """
        Same name as the method we override as we use it. Else django complains about an action that does not exists
        """

        if settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            # prevent deleting objects we do not have right for
            for application in Application.objects.all():
                if queryset.filter(application__name=application.name) and not request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + application.name):
                    queryset = queryset.exclude(application__name=application.name)
                    self.message_user(request, "You do not have right to delete variables from application %s" % (application.name,), level=messages.ERROR)
      
        return django_delete_selected(self, request, queryset)
    delete_selected.short_description = 'supprimer les variables'
    
    def unreserveVariable(self, request, queryset):
        """
        action permettant de déreserver les variables (enlever l'information de releaseDate)
        """
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        for var_id in selected:
            try:
                variable = Variable.objects.get(id=var_id)
                variable.releaseDate = None
                variable.save()
            except Exception as e:
                pass
    unreserveVariable.short_description = 'déréserver les variables'
    
