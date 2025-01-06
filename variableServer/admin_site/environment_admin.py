'''
Created on 12 déc. 2024

'''
from django import forms
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

class EnvironmentFilter(SimpleListFilter):
    """
    Depending on selected application, will show only related versions
    """
    title = 'Environment'
    parameter_name = 'environment'

    def lookups(self, request, model_admin):
        if 'application__id__exact' in request.GET:
            app_id = request.GET['application__id__exact']
            environments = set([c.environment for c in model_admin.model.objects.all().filter(application=app_id)])
        else:
            environments = set([c.environment for c in model_admin.model.objects.all()])
        return [(e.id, str(e)) for e in environments if e is not None] + [('_None_', 'None')]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '_None_':
                return queryset.filter(environment__id__exact=None)
            else:
                return queryset.filter(environment__id__exact=self.value())
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
    