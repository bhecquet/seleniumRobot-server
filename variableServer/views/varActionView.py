# -*- coding: utf-8 -*-
'''

'''
from variableServer.models import Variable
from django.http.response import HttpResponseRedirect
from django.contrib import admin, messages
from snapshotServer.models import Version, TestEnvironment, Application,\
    TestCase

def copyVariables(request):
    """
    Copie un ensemble de variable et modifie le/les paramètres sélectionnés
    """
    
    variableIds = [int(id) for id in request.POST['ids'].split(',')]
    
    try:
        test = TestCase.objects.get(id=int(request.POST['test']))
    except:
        test = None
        
    try:
        environment = TestEnvironment.objects.get(id=int(request.POST['environment']))
    except:
        environment = None
        
    try:
        version = Version.objects.get(id=int(request.POST['version']))
    except:
        version = None
        
    try:
        application = Application.objects.get(id=int(request.POST['application']))
    except:
        application = None
    
    # initialisation du message   
    from variableServer.admin import VariableAdmin 
    varAdmin = VariableAdmin(Variable, admin.site)
   
    # pour chaque variable, on va copier son contenu dans une nouvelle variable
    for variableId in variableIds:
        try:
            variable = Variable.objects.get(id=variableId)
            
            newVariable = Variable(name=variable.name, 
                                   value=variable.value, 
                                   application=application,
                                   environment=environment, 
                                   version=version, 
                                   test=test, 
                                   releaseDate=None,
                                   internal=variable.internal,
                                   description=variable.description)
            newVariable.save()
            varAdmin.message_user(request, "la variable %s a été copiée" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            varAdmin.message_user(request, "la variable d'id %d n'a pas été copiée: %s" % (variableId, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])

def changeVariables(request):
    """
    modifie un ensemble de variables avec le/les paramètres sélectionnés
    """
    
    variableIds = [int(id) for id in request.POST['ids'].split(',')]
    
    try:
        test = TestCase.objects.get(id=int(request.POST['test']))
    except:
        test = None
        
    try:
        environment = TestEnvironment.objects.get(id=int(request.POST['environment']))
    except:
        environment = None
        
    try:
        version = Version.objects.get(id=int(request.POST['version']))
    except:
        version = None
        
    try:
        application = Application.objects.get(id=int(request.POST['application']))
    except:
        application = None
    
    # initialisation du message    
    from variableServer.admin import VariableAdmin
    varAdmin = VariableAdmin(Variable, admin.site)
   
    # pour chaque variable, on va copier son contenu dans une nouvelle variable
    for variableId in variableIds:
        try:
            variable = Variable.objects.get(id=variableId)
            
            variable.application = application
            variable.version = version
            variable.environment = environment
            variable.test = test
            
            variable.save()
            varAdmin.message_user(request, "la variable %s a été modifiée" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            varAdmin.message_user(request, "la variable d'id %d n'a pas été modifiée: %s" % (variableId, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])



