'''
Created on 15 sept. 2017

@author: s047432
'''
import datetime
import time
import logging

from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics, permissions, filters
from rest_framework.exceptions import ValidationError

from variableServer.models import Variable, TestEnvironment, Version, TestCase
from variableServer.utils.utils import updateVariables
from variableServer.views.serializers import VariableSerializer
from variableServer.exceptions.AllVariableAlreadyReservedException import AllVariableAlreadyReservedException
from django.utils import timezone
from builtins import ValueError
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from commonsServer.views.viewsets import ApplicationSpecificFilter, BaseViewSet,\
    ApplicationSpecificViewSet
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissions,\
    ApplicationPermissionChecker
from django.conf import settings
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin

logger = logging.getLogger(__name__)

class Ping(APIView):
    
    # allow anyone on this view
    queryset = Variable.objects.none()
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        return Response("OK")
    
class VariableQuerySet(list):

    def __init__(self, *args, **kwargs):
        self.model = Variable
        super().__init__(*args, **kwargs)

    def filter(self, *args, **kwargs):
        
        return VariableQuerySet(self._filter(*args, **kwargs))

    def order_by(self, *args, **kwargs):
        return self
    
    def get(self, *args, **kwargs):
        new_list = self._filter(*args, **kwargs)
        if not new_list:
            raise ValueError            
                    
        return new_list[0]
    
    def _filter(self, *args, **kwargs):
        new_list = []
        for key, value in kwargs.items():
            for el in self:
                if str(getattr(el, key, None)) == str(value):
                    new_list.append(el)
                    
        return new_list
    
class VariableFilter(ApplicationSpecificFilter): 
    
    def _filter_get_queryset(self, request, queryset, view):
        """
        Filter to apply when GET method is called
        We return a list of variables
        """
        version_id = request.query_params.get('version', None)
        application_id = request.query_params.get('application', None)
        environment_id = request.query_params.get('environment', None)
        test_id = request.query_params.get('test', None)
        older_than = int(request.query_params.get('olderThan', '0'))
        reservation_duration = int(request.query_params.get('reservationDuration', '900'))
        variable_name = request.query_params.get('name', None)
        variable_value = request.query_params.get('value', None)
        reserve_reservable_variables = request.query_params.get('reserve', 'true') == 'true'
        
        version_name = 'N/A'
        application_name = 'N/A'
        environment_name = 'N/A'
        test_name = 'N/A'
         
        # return all variables if no filter is provided
        if 'pk' in view.kwargs:
            return queryset.filter(pk=view.kwargs['pk'])
        
        if not version_id:
            raise ValidationError("version parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            version = get_object_or_404(Version, pk=version_id)
            version_name = version.name
            application_name = version.application.name
        except ValueError as e:
            if not application_id:
                raise ValidationError("application parameter is mandatory when version is given as its name. Typical request is http://<host>:<port>/variable/api/variable?application=<app_name>&version=<version_name>&environment=<id_env>&test=<id_test>")
            version = get_object_or_404(Version, name=version_id, application__name=application_id)
            version_name = version.name
            application_name = application_id
        
        if not environment_id:
            raise ValidationError("environment parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            environment = get_object_or_404(TestEnvironment, pk=environment_id)
            environment_name = environment.name
        except ValueError as e:
            environment = get_object_or_404(TestEnvironment, name=environment_id)
            environment_name = environment.name
        
        if test_id:
            try:
                test = get_object_or_404(TestCase, pk=test_id)
                test_name = test.name
            except ValueError as e:
                test = get_object_or_404(TestCase, name=test_id)
                test_name = test.name
        else:
            test = None
            
        # get list of all variables that applies (variables that live forever and those which have not been obsolated
        all_variables = queryset.filter(timeToLive__lte=0) | queryset.filter(timeToLive__gt=0, creationDate__lt=timezone.now() - datetime.timedelta(older_than))
        
        variables = all_variables.filter(application=None, version=None, environment=None, test=None)
        
        # variables specific to one of the parameters, the other remain null
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=None, test=None))
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=None, test=None))
        
        # for each queryset depending on environment, we will first get the generic environment related variable and then update them
        # with the specific environment ones
        # for that purpose, we build the list of environments, first one is the most generic one, the latest is the most precise
        environment_tree = [environment] + environment.get_parent_environments()
        environment_tree.reverse()

        # environment specific variables
        for env in environment_tree:
            variables = updateVariables(variables, all_variables.filter(application=None, version=None, test=None, environment=env))
        
        # application / test specific variables
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=None, test=test))
        
        # more precise variables
        # application / environment specific variables
        for env in environment_tree:
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=env, test=None))
        
        # application / version/ environment specific variables
        for env in environment_tree:
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=env, test=None))
        
        if test:
            # application / environment / test specific variables
            for env in environment_tree:
                variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=env, test=test))
           
            # application / version / environment / test specific variables
            for env in environment_tree:
                variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=env, test=test))
        
        # in case name is provided, filter variables
        if variable_name:
            variables = variables.filter(name=variable_name)
            
        # in case value is provided, filter variables
        if variable_value:
            variables = variables.filter(value=variable_value)
            
        variable_names = list(set([v.name for v in variables]))
            
        filtered_variables = Variable.objects.select_for_update().filter(releaseDate=None).filter(id__in=[var.id for var in variables])
        
        with transaction.atomic():
            
            unique_variable_list = self._unique_variable(filtered_variables)
            
            # check we still have all variables after filtering. Else test may fail
            filtered_variable_names = list(set([v.name for v in unique_variable_list]))
            if (len(filtered_variable_names) < len(variable_names)):
                raise AllVariableAlreadyReservedException([v for v in variable_names if v not in filtered_variable_names])
            
            initial_list = []
            if reserve_reservable_variables:            
                initial_list = [v for v in self._reserve_reservable_variables(unique_variable_list, application_name, version_name, environment_name, test_name, reservation_duration)]
            else:
                initial_list = [v for v in unique_variable_list]
                
        initial_list += self._get_linked_application_variables(all_variables, version.application, environment_tree)
        
        return initial_list
    
    def _filter_delete_queryset(self, request, queryset, view):
        """
        Only allow "internal" variables deletion
        """
        return queryset.filter(pk=view.kwargs['pk'], internal=True)
    
    def filter_queryset(self, request, queryset, view):
        
        if request.method == "GET":
            variable_list = self._filter_get_queryset(request, queryset, view)
            permission = 'variableServer.view_%s' % queryset.model._meta.model_name
        elif request.method == "DELETE":
            variable_list = self._filter_delete_queryset(request, queryset, view)
            permission = 'variableServer.delete_%s' % queryset.model._meta.model_name
        # for POST / PATCH / PUT requests, further filtering is done, so we need a queryset
        # moreover, no filtering needs to be done for these
        else: 
            return queryset

        if view.bypass_application_permissions():
            return VariableQuerySet(variable_list)
        
        allowed_aplications = ApplicationPermissionChecker.get_allowed_applications(request)
        
        filtered_variables = [v for v in variable_list if v.application and v.application.name in allowed_aplications]
        return VariableQuerySet(filtered_variables)
    
    def _unique_variable(self, variable_query_set):
        """
        render a list where each variable is unique (according to it's name)
        list is randomized, so that when several variables have the same name, we do not render always the same
        
        There is a better way to return queryset than filtering on pk, using 'variable_query_set.order_by().distinct("name")'
        but
            - there is still ordering
            - unittest won't be possible due to the fact that distinct(field) is postgre only
        """

        existing_variable_names = []
        unique_variable_list = []
        initial_list = list(variable_query_set)
        random.shuffle(initial_list)
         
        for variable in initial_list:
            if variable.name not in existing_variable_names:
                unique_variable_list.append(variable)
                existing_variable_names.append(variable.name)
        return variable_query_set.filter(pk__in=[v.pk for v in unique_variable_list])

    def _reserve_reservable_variables(self, variable_list, application, version, environment, test, reservation_duration):
        """
        among all variables of the queryset, mark all variables as reserved (releaseDate not null) when the are flagged as reservable
        Release will occur 15 mins after now
        
        @param reservation_duration: number of seconds the variables will be reserved
        """
        for variable in variable_list:
            if variable.reservable:
                variable.releaseDate = timezone.now() + datetime.timedelta(seconds=reservation_duration)
                variable.save()
                logger.info("reserve variable [%d] %s=%s for (application=%s, version=%s, environment=%s, test=%s)" % (variable.id, variable.name, variable.value, application, version, environment, test))
                
        return variable_list
    
    def _get_linked_application_variables(self, all_variables, application, environment_tree):
        """
        Get all variables of the applications linked to the requested application
        """
        
        linked_application_variables = Variable.objects.none()
        if application.linkedApplication:
            for linked_application in application.linkedApplication.all():
                linked_application_variables = updateVariables(linked_application_variables, all_variables.filter(application=linked_application, version=None, environment=None, test=None, reservable=False))
            
                for env in environment_tree:
                    linked_application_variables = updateVariables(linked_application_variables, all_variables.filter(application=linked_application, version=None, environment=env, test=None, reservable=False))
 
        updated_linked_application_variables = []
        for var in linked_application_variables:
            updated_linked_application_variables.append(Variable(name=var.nameWithApp, value=var.value, application=var.application, version=var.version, environment=var.environment))
 
        return updated_linked_application_variables
    
       

class VariableList(ApplicationSpecificViewSet):
    
    serializer_class = VariableSerializer
    filter_backends = [VariableFilter]
    permission_classes = [ApplicationSpecificPermissions]
    queryset = Variable.objects.none()
    
    def _reset_past_release_dates(self):
        for var in Variable.objects.filter(releaseDate__lte=time.strftime('%Y-%m-%d %H:%M:%S%z')):
            var.releaseDate = None
            var.save()
            logger.info("unreserve variable [%d] automatically %s=%s " % (var.id, var.name, var.value))
        
    def _delete_old_variables(self):
        """
        Delete variables which contains a positive value for 'timeToLive' and which are still there whereas they expired
        """
        for var in Variable.objects.filter(timeToLive__gt=0):
            if timezone.now() - datetime.timedelta(var.timeToLive) > var.creationDate:
                var.delete()
                
    
    def get_queryset(self):
        return Variable.objects.all()
    

    def get(self, request, *args, **kwargs):
        """
        Get all variables corresponding to requested args
        """
        # reset 
        self._reset_past_release_dates()
        
        # remove old variables
        self._delete_old_variables()
        
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        return response
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        
        release_date = request.data.get('releaseDate', None)
        if release_date == '':
            try:
                variable = get_object_or_404(Variable, pk=int(kwargs['pk']))
                logger.info("unreserve variable [%d] %s=%s " % (variable.id, variable.name, variable.value))
            except:
                pass
        
        return self.partial_update(request, *args, **kwargs)
    
    