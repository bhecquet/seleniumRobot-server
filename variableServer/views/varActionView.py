# -*- coding: utf-8 -*-
'''

'''
from variableServer.models import Variable
from django.http.response import HttpResponseRedirect
from django.contrib import admin, messages
from variableServer.models import Version, TestEnvironment, Application,\
    TestCase
from variableServer.exceptions.VariableSetException import VariableSetException
from seleniumRobotServer.settings import RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN as FLAG_RESTRICT_APP

def copyVariables(request):
    """
    Copy a set of variables and change some of the parameters
    """
    
    variableIds = [int(id) for id in request.POST['ids'].split(',')]
    
    try:
        tests = TestCase.objects.filter(id__in=request.POST.getlist('test'))
    except:
        tests = []
        
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
        
    try:
        reservable = request.POST['reservable'] == 'on'
    except:
        reservable = False
    
    # init message   
    from variableServer.admin import VariableAdmin 
    varAdmin = VariableAdmin(Variable, admin.site)
    
    if FLAG_RESTRICT_APP and application and not request.user.has_perm('commonsServer.can_view_application_' + application.name):
        varAdmin.message_user(request, "You don't have right to copy variable to application %s" % (application.name,), level=messages.ERROR)
        return HttpResponseRedirect(request.POST['nexturl'])

   
    # copy content of each variable in a new variable
    for variableId in variableIds:
        try:
            variable = Variable.objects.get(id=variableId)
            
            newVariable = Variable(name=variable.name, 
                                   value=variable.value, 
                                   application=application,
                                   environment=environment, 
                                   reservable=reservable,
                                   version=version, 
                                   releaseDate=None,
                                   internal=variable.internal,
                                   description=variable.description)
            newVariable.save()
            for test in tests:
                newVariable.test.add(test)
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
        tests = TestCase.objects.filter(id__in=request.POST.getlist('test'))
    except:
        tests = []
        
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
        
    try:
        reservable = request.POST['reservable'] == 'on'
    except:
        reservable = False
    
    # init message     
    from variableServer.admin import VariableAdmin
    varAdmin = VariableAdmin(Variable, admin.site)
    
    if FLAG_RESTRICT_APP and application and not request.user.has_perm('commonsServer.can_view_application_' + application.name):
        varAdmin.message_user(request, "You don't have right to update variable to application %s" % (application.name,), level=messages.ERROR)
        return HttpResponseRedirect(request.POST['nexturl'])
   
    # update each variable with the new parameters
    for variableId in variableIds:
        try:
            variable = Variable.objects.get(id=variableId)
            
            if FLAG_RESTRICT_APP and variable.application and not request.user.has_perm('commonsServer.can_view_application_' + variable.application.name):
                raise VariableSetException("No right to change variable belonging to application %s" % variable.application.name)
            
            variable.application = application
            variable.version = version
            variable.environment = environment
            variable.reservable = reservable
            variable.save()
            
            variable.test.clear()
            for test in tests:
                variable.test.add(test)
            
            varAdmin.message_user(request, "Variable %s has been modified" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            varAdmin.message_user(request, "Variable with id %d has not been modified: %s" % (variableId, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])



