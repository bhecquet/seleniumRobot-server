# -*- coding: utf-8 -*-
'''

'''
from variableServer.models import Variable
from django.http.response import HttpResponseRedirect
from django.contrib import admin, messages
from variableServer.models import Version, TestEnvironment, Application,\
    TestCase
from variableServer.admin_site.variable_admin import VariableAdmin
from django.conf import settings
from seleniumRobotServer.permissions.permissions import APP_SPECIFIC_PERMISSION_PREFIX

def copy_variables(request):
    """
    Copy a set of variables and change some of the parameters
    """

    application, version, environment, tests, reservable, variable_ids = _get_input_data(request)
    
    # init message   
    var_admin = VariableAdmin(Variable, admin.site)
        
    global_permission = request.user.has_perm('variableServer.add_variable')
    has_permission, related_application = _has_application_permission(request, application, variable_ids, global_permission)
    if not has_permission:
        var_admin.message_user(request, "You don't have right to copy variables to application %s" % (related_application,), level=messages.ERROR)
        return HttpResponseRedirect(request.POST['nexturl'])
    
    # copy content of each variable in a new variable
    for variable_id in variable_ids:
        try:
            variable = Variable.objects.get(id=variable_id)
            
            new_variable = Variable(name=variable.name, 
                                   value=variable.value, 
                                   application=application,
                                   environment=environment, 
                                   reservable=reservable,
                                   version=version, 
                                   releaseDate=None,
                                   internal=variable.internal,
                                   description=variable.description)
            new_variable.save()
            for test in tests:
                new_variable.test.add(test)
            var_admin.message_user(request, "Variable %s has been copied" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            var_admin.message_user(request, "Variable with id %d has not been copied: %s" % (variable_id, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])

def change_variables(request):
    """
    Change a set of variables with the given parameters
    """
    application, version, environment, tests, reservable, variable_ids = _get_input_data(request)
    
    # init message     
    var_admin = VariableAdmin(Variable, admin.site)
    
    global_permission = request.user.has_perm('variableServer.change_variable')
    has_permission, related_application = _has_application_permission(request, application, variable_ids, global_permission)
    if not has_permission:
        var_admin.message_user(request, "You don't have right to change variables to application %s" % (related_application,), level=messages.ERROR)
        return HttpResponseRedirect(request.POST['nexturl'])
   
    # update each variable with the new parameters
    for variable_id in variable_ids:
        try:
            variable = Variable.objects.get(id=variable_id)
            variable.application = application
            variable.version = version
            variable.environment = environment
            variable.reservable = reservable
            variable.save()
            
            variable.test.clear()
            for test in tests:
                variable.test.add(test)
            
            var_admin.message_user(request, "Variable %s has been modified" % (variable.name,), level=messages.INFO)
            
        except Exception as e:
            var_admin.message_user(request, "Variable with id %d has not been modified: %s" % (variable_id, str(e)), level=messages.ERROR)
        
    return HttpResponseRedirect(request.POST['nexturl'])

def _get_input_data(request):
    variable_ids = [int(id) for id in request.POST['ids'].split(',')]
    
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
        
    return application, version, environment, tests, reservable, variable_ids

def _has_application_permission(request, application, variable_ids, has_global_permission):
    """
    Check if user has permission on 'application', or any application related to variable
    @param request: The request
    @param application: the application user want to copy to / to modify
    @param variable_ids: the variables that will be impacted by change
    @param has_global_permission: whether the user has global permission on any application
    """
    
    # global permission has priority over application permission
    if has_global_permission:
        return has_global_permission, application
    
    if settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
        # check user has permission to destination application
        if application and not request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + application.name):
            return False, application
        
        # user cannot change to 'no application'
        if not application:
            return False, 'None'
            
        # check user has permission to source application
        for app in [var.application for var in Variable.objects.filter(id__in=variable_ids)]:
            if app is None or not request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + app.name):
                return False, app
            
    else:
        return has_global_permission, application
    
    return True, application

