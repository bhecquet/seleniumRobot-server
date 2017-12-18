'''
Created on 15 sept. 2017

@author: s047432
'''
from datetime import timezone
import datetime
import time

from django.db.models import Q
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, generics
from rest_framework.exceptions import ValidationError

from seleniumRobotServer.wsgi import application
from variableServer.models import Variable, TestEnvironment, Version, TestCase
from variableServer.utils.utils import SPECIAL_NONE, SPECIAL_NOT_NONE, \
    updateVariables
from variableServer.views.serializers import VariableSerializer
from variableServer.exceptions.AllVariableAlreadyReservedException import AllVariableAlreadyReservedException


def ping(request):
    return HttpResponse("OK")

class VariableList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  generics.GenericAPIView):
    
    serializer_class = VariableSerializer
    
    def _resetPastReleaseDates(self):
        for var in Variable.objects.filter(releaseDate__lte=time.strftime('%Y-%m-%d %H:%M:%S%z')):
            var.releaseDate = None
            var.save()
        
    
    def get_queryset(self):
        """

        """
        versionId = self.request.query_params.get('version', None)
        if not versionId:
            raise ValidationError("version parameter is mandatory")
        version = get_object_or_404(Version, pk=versionId)
        
        environmentId = self.request.query_params.get('environment', None)
        if not environmentId:
            raise ValidationError("environment parameter is mandatory")
        environment = get_object_or_404(TestEnvironment, pk=environmentId)
        
        testId = self.request.query_params.get('test', None)
        if not testId:
            raise ValidationError("test parameter is mandatory")
        test = get_object_or_404(TestCase, pk=testId)
        
        variables = Variable.objects.filter(application=None, version=None, environment=None, test=None)
        
        # variables specific to one of the parameters, the other remain null
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=None, test=None))
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=version, environment=None, test=None))
        
        # for each queryset depending on environment, we will first get the generic environment related variable and then update them
        # with the specific environment ones
        if environment.genericEnvironment:
            genericEnvironment = environment.genericEnvironment
        else:
            genericEnvironment = environment
        
        # environment specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=None, version=None, test=None, environment=genericEnvironment))
        variables = updateVariables(variables, Variable.objects.filter(application=None, version=None, test=None, environment=environment))
        
        # application / test specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=None, test=test))
        
        # more precise variables
        # application / environment specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=genericEnvironment, test=None))
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=environment, test=None))
        
        # application / version/ environment specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=version, environment=genericEnvironment, test=None))
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=version, environment=environment, test=None))
        
        # application / environment / test specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=genericEnvironment, test=test))
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=None, environment=environment, test=test))
        
        # application / version / environment / test specific variables
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=version, environment=genericEnvironment, test=test))
        variables = updateVariables(variables, Variable.objects.filter(application=version.application, version=version, environment=environment, test=test))
        
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
        """
        existingVariableNames = []
        uniqueVariableList = []
        for variable in variableQuerySet:
            if variable.name not in existingVariableNames:
                uniqueVariableList.append(variable)
                existingVariableNames.append(variable.name)
        return uniqueVariableList
    
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
                variable.releaseDate = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=900)
                variable.save()
                
        return variableList

    def get(self, request, *args, **kwargs):
        """
        Get all variables corresponding to requested args
        """
        # reset 
        self._resetPastReleaseDates()
        
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        return response
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    