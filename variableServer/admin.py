from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django import forms
from variableServer.models import Variable, TestCase, Application, Version
from django.template.context_processors import csrf
from django.shortcuts import render_to_response
from variableServer.models import TestEnvironment
from seleniumRobotServer.settings import RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN as FLAG_RESTRICT_APP

def isUserAuthorized(user):
    """
    Renvoie True si l'utilisateur est autorisé à voir les variables protégées
    @param user: l'utilisateur dont on vérifie les droits
    """
    if not user:
        return False
    if (user 
        and user.is_authenticated 
        and (user.is_superuser 
             or user.has_perm('variableServer.see_protected_var'))):
        return True
    else:
        return False
    
class BaseServerModelAdmin(admin.ModelAdmin):
    """
    Base class to restrict access to application objects the user has rights to see
    
    TODO: unit tests not created!!!
    """
    
    def _has_app_permission(self, global_permission, request, obj=None):
        """
        Whether user has rights on this application
        """
        if not FLAG_RESTRICT_APP:
            return global_permission
        
        if global_permission and request.method == 'POST' and request.POST.get('application'):
            application = Application.objects.get(pk=int(request.POST['application']))
            if not request.user.has_perm('commonsServer.can_view_application_' + application.name):
                return False
            
        elif global_permission and obj and obj.application and not request.user.has_perm('commonsServer.can_view_application_' + obj.application.name):
            return False
            
        return global_permission
    
    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        """
        perm = super(BaseServerModelAdmin, self).has_add_permission(request)

        return perm and self._has_app_permission(perm, request)

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_change_permission(request, obj)
        
        return perm and self._has_app_permission(perm, request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_change_permission(request, obj)
                
        return perm and self._has_app_permission(perm, request, obj)

class VariableForm(forms.ModelForm):

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
        
     
        # affichage des champs en fonction de l'utilisateur connecté
        # si un champ est protégé, la valeur ne doit être visible que de ceux qui ont la permission
        # see_protected_var
        if self.initial.get('protected', False) and not isUserAuthorized(user):
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
            initialValue = self.initial.get(field_name, field.initial)
            if initialValue:
                return initialValue.all()
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
    list_filter = ('application', 'version', 'environment', 'internal')
    search_fields = ['name', 'value']
    form = VariableForm
    actions = ['delete_selected', 'copyTo', 'changeValuesAtOnce', 'unreserveVariable']
    
    def get_list_display(self, request):
        if isUserAuthorized(request.user):
            return self.list_display
        else:
            return self.list_display_protected
        
    def get_queryset(self, request):
        """
        Filter the returned variables with the application user is allowed to see
        """
        qs = super(VariableAdmin, self).get_queryset(request)
        
        if not FLAG_RESTRICT_APP:
            return qs
         
        for application in Application.objects.all():
            if not request.user.has_perm('commonsServer.can_view_application_' + application.name):
                qs = qs.exclude(application__name=application.name)
                 
        return qs

    def save_model(self, request, obj, form, change):
        """
        Dans le cas où l'utilisateur n'est pas habilité à voir les variables protégées (et donc, à les modifier)
        cette méthode va remettre les valeurs par défaut pour 'value' et 'protected'
        """
        
        user = request.user
        
        # avant de sauvegarder, on récupère de la base le flag 'protected'
        try:
            dbObj = Variable.objects.get(id=obj.id)
    
            # dans le cas où l'utilisateur n'est pas habilité à voir la variable, il ne pourra pas la modifier
            if dbObj.protected and not isUserAuthorized(user):
                obj.protected = dbObj.protected
                obj.value = dbObj.value
        except:
            # on peut se trouver ici dans le cas d'un ajout de variable, auquel cas, celle-ci n'existe pas déjà en BDD
            pass
        
        admin.ModelAdmin.save_model(self, request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """
        redefinition de la méthode pour pouvoir exploiter l'utilisateur dans le formulaire
        """
        try:
            obj.user = request.user
        except:
            pass

        return admin.ModelAdmin.get_form(self, request, obj=obj, **kwargs)
    
    def _getDefaultValues(self, selectedVariables):
        """
        Retourne les valeurs par défaut à sélectionner dans l'interface de copy/modification sous forme de dictionnaire
        """
        refVariable = Variable.objects.get(id=int(selectedVariables[0]))
        defaultValues = {'environment': refVariable.environment,
                         'application': refVariable.application,
                         'test': refVariable.test,
                         'version': refVariable.version,
                         'reservable': refVariable.reservable
                         }
        
        for variableId in selectedVariables[1:]:
            variable = Variable.objects.get(id=int(variableId))
            if variable.environment != refVariable.environment:
                defaultValues['environment'] = None
            if variable.application != refVariable.application:
                defaultValues['application'] = None
            # take ManyToMany relationship for test into account
            if not (variable.test and refVariable.test) or list(variable.test.all()) != list(refVariable.test.all()):
                defaultValues['test'] = None
            if variable.version != refVariable.version:
                defaultValues['version'] = None
            if variable.reservable != refVariable.reservable:
                defaultValues['reservable'] = False
            
        return defaultValues
    
    def copyTo(self, request, queryset):
        """
        Action permettant de copier plusieurs variables d'un coup
        On reprend les valeurs communes des variables pour les proposer au moment de l'écran de saisie
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)

        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._getDefaultValues(selected)),
                'queryString': request.META['QUERY_STRING']} # permettra de revenir à la liste des variables filtrée
        args.update(csrf(request))

        return render_to_response("variableServer/admin/copyTo.html", args)
    copyTo.short_description = 'copier les variables'
    
    def changeValuesAtOnce(self, request, queryset):
        """
        Action permettant de modifier plusieurs variables d'un coup
        On reprend les valeurs communes des variables pour les proposer au moment de l'écran de saisie
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        args = {'ids': ','.join(selected), 
                'form': VariableForm2(initial=self._getDefaultValues(selected)),
                'queryString': request.META['QUERY_STRING']} # permettra de revenir à la liste des variables filtrée
        args.update(csrf(request))

        return render_to_response("variableServer/admin/changeTo.html", args)
    changeValuesAtOnce.short_description = 'modifier les variables'
    
    def delete_selected(self, request, queryset):
        """
        Same name as the method we override as we use it. Else django complains about an action that does not exists
        """
        
        if FLAG_RESTRICT_APP:
            # prevent deleting objects we do not have right for
            for application in Application.objects.all():
                if queryset.filter(application__name=application.name) and not request.user.has_perm('commonsServer.can_view_application_' + application.name):
                    queryset = queryset.exclude(application__name=application.name)
                    self.message_user(request, "You do not have right to delete variables from application %s" % (application.name,), level=messages.ERROR)
      
        return django_delete_selected(self, request, queryset)
    delete_selected.short_description = 'supprimer les variables'
    
    def unreserveVariable(self, request, queryset):
        """
        action permettant de déreserver les variables (enlever l'information de releaseDate)
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        for varId in selected:
            try:
                variable = Variable.objects.get(id=varId)
                variable.releaseDate = None
                variable.save()
            except:
                pass
    unreserveVariable.short_description = 'déréserver les variables'
    
class EnvironmentForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(EnvironmentForm, self).__init__(*args, **kwargs)
        self.fields['genericEnvironment'].required = False
   
class EnvironmentAdmin(admin.ModelAdmin):
    list_filter = ('genericEnvironment', )
    list_display = ('name', 'genericEnvironment')
    actions = ['delete_selected']
    form = EnvironmentForm
    
    
class TestCaseForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(TestCaseForm, self).__init__(*args, **kwargs)

class TestCaseAdmin(BaseServerModelAdmin): 
    list_display = ('name', 'application')
    list_filter = ('application',)
    form = TestCaseForm
    actions = ['delete_selected']

    def get_queryset(self, request):
        """
        Filter the returned versions with the application user is allowed to see
        """
        qs = super(TestCaseAdmin, self).get_queryset(request)
        
        if not FLAG_RESTRICT_APP:
            return qs
         
        for application in Application.objects.all():
            if not request.user.has_perm('commonsServer.can_view_application_' + application.name):
                qs = qs.exclude(application__name=application.name)
                 
        return qs  
    
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', )

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
                        'fields': ('name',),
                        'description': '<div style="font-size: 16px;color: red;">All tests / variables must be deleted before this application can be deleted</div>'}
                  ),
                 )
               
    def has_delete_permission(self, request, obj=None):
        """
        Do not display delete button if some tests / variables are linked to this application
        """
        
        canDelete = admin.ModelAdmin.has_delete_permission(self, request, obj=obj)
        
        # when no object provided, default behavior
        if not obj:
            return canDelete
        
        # check for linked test cases and variables
        if len(TestCase.objects.filter(application=obj)) and len(Variable.objects.filter(application=obj)):
            return False
        else:
            return True and canDelete 
        
class VersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        
class VersionAdmin(BaseServerModelAdmin): 
    list_display = ('name', 'application')
    list_filter = ('application',)
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
                        'fields': ('name', 'application', 'linkedVersions'),
                        'description': '<div style="font-size: 16px;color: red;">This version will be deleted when all linked variables will be deleted</div>'}
                  ),
                 )
            
            
            
    def has_delete_permission(self, request, obj=None):
        """
        Do not display delete button if some tests / variables are linked to this application
        """
        
        canDelete = admin.ModelAdmin.has_delete_permission(self, request, obj=obj)
        
        # when no object provided, default behavior
        if not obj:
            return canDelete
        
        # check for linked variables
        if len(Variable.objects.filter(version=obj)):
            return False
        else:
            return True and canDelete  
        
    def get_queryset(self, request):
        """
        Filter the returned versions with the application user is allowed to see
        """
        qs = super(VersionAdmin, self).get_queryset(request)
        
        if not FLAG_RESTRICT_APP:
            return qs
         
        for application in Application.objects.all():
            if not request.user.has_perm('commonsServer.can_view_application_' + application.name):
                qs = qs.exclude(application__name=application.name)
                 
        return qs  

# Register your models here.
admin.site.disable_action('delete_selected')
admin.site.register(Application, ApplicationAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(TestEnvironment, EnvironmentAdmin)