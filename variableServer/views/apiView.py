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


def ping(request):
    return HttpResponse("OK")

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
        """

        """
        
        versionId = self.request.query_params.get('version', None)
        applicationId = self.request.query_params.get('application', None)
        environmentId = self.request.query_params.get('environment', None)
        testId = self.request.query_params.get('test', None)
        olderThan = int(self.request.query_params.get('olderThan', '0'))
         
        # return all variables if no filter is provided
        if 'pk' in self.kwargs:
            return Variable.objects.filter(pk=self.kwargs['pk'])
        
        if not versionId:
            raise ValidationError("version parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            version = get_object_or_404(Version, pk=versionId)
        except ValueError as e:
            if not applicationId:
                raise ValidationError("application parameter is mandatory when version is given as its name. Typical request is http://<host>:<port>/variable/api/variable?application=<app_name>&version=<version_name>&environment=<id_env>&test=<id_test>")
            version = get_object_or_404(Version, name=versionId, application__name=applicationId)
        
        if not environmentId:
            raise ValidationError("environment parameter is mandatory. Typical request is http://<host>:<port>/variable/api/variable?version=<id_version>&environment=<id_env>&test=<id_test>")
        try:
            environment = get_object_or_404(TestEnvironment, pk=environmentId)
        except ValueError as e:
            environment = get_object_or_404(TestEnvironment, name=environmentId)
        
        if testId:
            try:
                test = get_object_or_404(TestCase, pk=testId)
            except ValueError as e:
                test = get_object_or_404(TestCase, name=testId)
        else:
            test = None
        
        allVariables = Variable.objects.filter(timeToLive__lte=0) | Variable.objects.filter(timeToLive__gt=0, creationDate__lt=timezone.now() - datetime.timedelta(olderThan))
        
        variables = allVariables.filter(application=None, version=None, environment=None, test=None)
        
        # variables specific to one of the parameters, the other remain null
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=None, test=None))
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=version, environment=None, test=None))
        
        # for each queryset depending on environment, we will first get the generic environment related variable and then update them
        # with the specific environment ones
        if environment.genericEnvironment:
            genericEnvironment = environment.genericEnvironment
        else:
            genericEnvironment = environment
        
        # environment specific variables
        variables = updateVariables(variables, allVariables.filter(application=None, version=None, test=None, environment=genericEnvironment))
        variables = updateVariables(variables, allVariables.filter(application=None, version=None, test=None, environment=environment))
        
        # application / test specific variables
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=None, test=test))
        
        # more precise variables
        # application / environment specific variables
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=genericEnvironment, test=None))
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=environment, test=None))
        
        # application / version/ environment specific variables
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=version, environment=genericEnvironment, test=None))
        variables = updateVariables(variables, allVariables.filter(application=version.application, version=version, environment=environment, test=None))
        
        if test:
            # application / environment / test specific variables
            variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=genericEnvironment, test=test))
            variables = updateVariables(variables, allVariables.filter(application=version.application, version=None, environment=environment, test=test))
        
            # application / version / environment / test specific variables
            variables = updateVariables(variables, allVariables.filter(application=version.application, version=version, environment=genericEnvironment, test=test))
            variables = updateVariables(variables, allVariables.filter(application=version.application, version=version, environment=environment, test=test))
        
        variableNames = list(set([v.name for v in variables]))
        
        uniqueVariableList = self._uniqueVariable(variables.filter(releaseDate=None))
        
        # check we still have all variables after filtering. Else test may fail
        filteredVariableNames = list(set([v.name for v in uniqueVariableList]))
        if (len(filteredVariableNames) < len(variableNames)):
            raise AllVariableAlreadyReservedException([v for v in variableNames if v not in filteredVariableNames])
        
        return self._reserveReservableVariables(uniqueVariableList)
        
    def _uniqueVariable(self, variableQuerySet):
        """
        render a list where each variable is unique (according to it's name)
        list is randomized, so that when several variables have the same name, we do not render always the same
        
        There is a better way to return queryset than filtering on pk, using 'variableQuerySet.order_by().distinct("name")'
        but
            - there is still ordering
            - unittest won't be possible due to the fact that distinct(field) is postgre only
        """

        existingVariableNames = []
        uniqueVariableList = []
        initialList = list(variableQuerySet)
        random.shuffle(initialList)
         
        for variable in initialList:
            if variable.name not in existingVariableNames:
                uniqueVariableList.append(variable)
                existingVariableNames.append(variable.name)
        return variableQuerySet.filter(pk__in=[v.pk for v in uniqueVariableList])
    
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
    
    