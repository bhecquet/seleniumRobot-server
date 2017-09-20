'''
Created on 4 mai 2017

@author: bhecquet
'''
from rest_framework import viewsets

from variableServer.models import Variable
from variableServer.views.serializers import VariableSerializer

    
class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.all()
    serializer_class = VariableSerializer
