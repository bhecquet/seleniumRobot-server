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
    Copy a set of variables and change some of the parameters
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
    
    # init message   
    from variableServer.admin import VariableAdmin 
    varAdmin = VariableAdmin(Variable, admin.site)
   
    # copy content of each variable in a new variable
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
            varAdmin.message_user(request, "Variable %s has been copied" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            varAdmin.message_user(request, "Variable with id %d has not been copied: %s" % (variableId, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])

def changeVariables(request):
    """
    Change a set of variables with the given parameters
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
    
    # init message     
    from variableServer.admin import VariableAdmin
    varAdmin = VariableAdmin(Variable, admin.site)
   
    # update each variable with the new parameters
    for variableId in variableIds:
        try:
            variable = Variable.objects.get(id=variableId)
            
            variable.application = application
            variable.version = version
            variable.environment = environment
            variable.test = test
            
            variable.save()
            varAdmin.message_user(request, "Variable %s has been modified" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            varAdmin.message_user(request, "Variable with id %d has not been modified: %s" % (variableId, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])



