'''
Created on 15 sept. 2017

@author: s047432
'''
import datetime
import time

from django.db.models import Q
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics
from rest_framework.exceptions import ValidationError

from seleniumRobotServer.wsgi import application
from variableServer.models import Variable, TestEnvironment, Version, TestCase,\
    Application
from variableServer.utils.utils import SPECIAL_NONE, SPECIAL_NOT_NONE, \
    updateVariables
from variableServer.views.serializers import VariableSerializer
from variableServer.exceptions.AllVariableAlreadyReservedException import AllVariableAlreadyReservedException
from django.utils import timezone
from builtins import ValueError
import random
from rest_framework.views import APIView
from rest_framework.response import Response

class Ping(APIView):
    
    queryset = Variable.objects.none()
    
    def get(self, request, *args, **kwargs):
        return Response("OK")

class VariableList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  generics.GenericAPIView):
    
    serializer_class = VariableSerializer
    
    queryset = Variable.objects.none()
    
    def _resetPastReleaseDates(self):
        for var in Variable.objects.filter(releaseDate__lte=time.strftime('%Y-%m-%d %H:%M:%S%z')):
            var.releaseDate = None
            var.save()
        
    def _deleteOldVariables(self):
        """
        Delete variables which contains a positive value for 'timeToLive' and which are still whereas they expired
        """
        for var in Variable.objects.filter(timeToLive__gt=0):
            if timezone.now() - datetime.timedelta(var.timeToLive) > var.creationDate:
                var.delete()
    
    def get_queryset(self):
        return Variable.objects.all()
    
    def filter_queryset(self, queryset):
        
        version_id = self.request.query_params.get('version', None)
        application_id = self.request.query_params.get('application', None)
        environment_id = self.request.query_params.get('environment', None)
        test_id = self.request.query_params.get('test', None)
        older_than = int(self.request.query_params.get('olderThan', '0'))
        variable_name = self.request.query_params.get('name', None)
        variable_value = self.request.query_params.get('value', None)
         
        # return all variables if no filter is provided
        if 'pk' in self.kwargs:
            return queryset.filter(pk=self.kwargs['pk'])
        
        if not version_id:
            raise ValidationError("version parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            version = get_object_or_404(Version, pk=version_id)
        except ValueError as e:
            if not application_id:
                raise ValidationError("application parameter is mandatory when version is given as its name. Typical request is http://<host>:<port>/variable/api/variable?application=<app_name>&version=<version_name>&environment=<id_env>&test=<id_test>")
            version = get_object_or_404(Version, name=version_id, application__name=application_id)
        
        if not environment_id:
            raise ValidationError("environment parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            environment = get_object_or_404(TestEnvironment, pk=environment_id)
        except ValueError as e:
            environment = get_object_or_404(TestEnvironment, name=environment_id)
        
        if test_id:
            try:
                test = get_object_or_404(TestCase, pk=test_id)
            except ValueError as e:
                test = get_object_or_404(TestCase, name=test_id)
        else:
            test = None
        
        all_variables = queryset.filter(timeToLive__lte=0) | queryset.filter(timeToLive__gt=0, creationDate__lt=timezone.now() - datetime.timedelta(older_than))
        
        variables = all_variables.filter(application=None, version=None, environment=None, test=None)
        
        # variables specific to one of the parameters, the other remain null
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=None, test=None))
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=None, test=None))
        
        # for each queryset depending on environment, we will first get the generic environment related variable and then update them
        # with the specific environment ones
        if environment.genericEnvironment:
            generic_environment = environment.genericEnvironment
        else:
            generic_environment = environment
        
        # environment specific variables
        variables = updateVariables(variables, all_variables.filter(application=None, version=None, test=None, environment=generic_environment))
        variables = updateVariables(variables, all_variables.filter(application=None, version=None, test=None, environment=environment))
        
        # application / test specific variables
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=None, test=test))
        
        # more precise variables
        # application / environment specific variables
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=generic_environment, test=None))
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=environment, test=None))
        
        # application / version/ environment specific variables
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=generic_environment, test=None))
        variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=environment, test=None))
        
        if test:
            # application / environment / test specific variables
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=generic_environment, test=test))
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=None, environment=environment, test=test))
        
            # application / version / environment / test specific variables
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=generic_environment, test=test))
            variables = updateVariables(variables, all_variables.filter(application=version.application, version=version, environment=environment, test=test))
        
        # in case name is provided, filter variables
        if variable_name:
            variables = variables.filter(name=variable_name)
            
        # in case value is provided, filter variables
        if variable_value:
            variables = variables.filter(value=variable_value)
        
        variable_names = list(set([v.name for v in variables]))
        
        unique_variable_list = self._uniqueVariable(variables.filter(releaseDate=None))
        
        # check we still have all variables after filtering. Else test may fail
        filtered_variable_names = list(set([v.name for v in unique_variable_list]))
        if (len(filtered_variable_names) < len(variable_names)):
            raise AllVariableAlreadyReservedException([v for v in variable_names if v not in filtered_variable_names])
        
        return self._reserveReservableVariables(unique_variable_list)
        
    def _uniqueVariable(self, variableQuerySet):
        """
        render a list where each variable is unique (according to it's name)
        list is randomized, so that when several variables have the same name, we do not render always the same
        
        There is a better way to return queryset than filtering on pk, using 'variableQuerySet.order_by().distinct("name")'
        but
            - there is still ordering
            - unittest won't be possible due to the fact that distinct(field) is postgre only
        """

        existing_variable_names = []
        unique_variable_list = []
        initial_list = list(variableQuerySet)
        random.shuffle(initial_list)
         
        for variable in initial_list:
            if variable.name not in existing_variable_names:
                unique_variable_list.append(variable)
                existing_variable_names.append(variable.name)
        return variableQuerySet.filter(pk__in=[v.pk for v in unique_variable_list])
    
    def _filterNotReservedVariables(self, variableList):
        """
        Remove all variables which are reserved
        """
    
    def _reserveReservableVariables(self, variableList):
        """
        among all variables of the queryset, mark all variables as reserved (releaseDate not null) when the are flagged as reservable
        Release will occur 15 mins after now
        """
        for variable in variableList:
            if variable.reservable:
                variable.releaseDate = timezone.now() + datetime.timedelta(seconds=900)
                variable.save()
                
        return variableList

    def get(self, request, *args, **kwargs):
        """
        Get all variables corresponding to requested args
        """
        # reset 
        self._resetPastReleaseDates()
        
        # remove old variables
        self._deleteOldVariables()
        
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        return response
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    