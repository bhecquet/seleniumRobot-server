from django.contrib import admin
from django import forms
from variableServer.models import Variable, TestCase, Application, Version
from django.template.context_processors import csrf
from django.shortcuts import render_to_response
from variableServer.models import TestEnvironment

def isUserAuthorized(user):
    """
    Renvoie True si l'utilisateur est autorisé à voir les variables protégées
    @param user: l'utilisateur dont on vérifie les droits
    """
    if not user:
        return False
    if (user 
        and user.is_authenticated() 
        and (user.is_superuser 
             or user.has_perm('variableServer.see_protected_var'))):
        return True
    else:
        return False

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

    class Meta:
        model = Variable
        fields = ['application', 'version', 'environment', 'test']

class VariableAdmin(admin.ModelAdmin):
    list_display = ('nameWithApp', 'value', 'application', 'environment', 'version', 'test', 'releaseDate')
    list_display_protected = ('nameWithApp', 'valueProtected', 'application', 'environment', 'version', 'test', 'releaseDate')
    list_filter = ('application', 'version', 'environment', 'internal')
    search_fields = ['name', 'value']
    form = VariableForm
    actions = ['copyTo', 'changeValuesAtOnce', 'unreserveVariable']
    
    def get_list_display(self, request):
        if isUserAuthorized(request.user):
            return self.list_display
        else:
            return self.list_display_protected

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
                         }
        
        for variableId in selectedVariables[1:]:
            variable = Variable.objects.get(id=int(variableId))
            if variable.environment != refVariable.environment:
                defaultValues['environment'] = None
            if variable.application != refVariable.application:
                defaultValues['application'] = None
            if variable.test != refVariable.test:
                defaultValues['test'] = None
            if variable.version != refVariable.version:
                defaultValues['version'] = None
            
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
    form = EnvironmentForm
    
    
class TestCaseForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(TestCaseForm, self).__init__(*args, **kwargs)

class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'application')
    list_filter = ('application',)
    form = TestCaseForm
    
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
        
class VersionAdmin(admin.ModelAdmin):
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

# Register your models here.
admin.site.register(Application, ApplicationAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(TestEnvironment, EnvironmentAdmin)