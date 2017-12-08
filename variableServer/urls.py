
from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers
from variableServer.views import varActionView, apiView
from variableServer.views.apiView import VariableList

urlpatterns = [
    url(r'^api/variable', VariableList.as_view(), name='variableApi'),
    url(r'^api', apiView.ping, name='variablePing'),
    
    url(r'copyVariables', varActionView.copyVariables, name='copyVariables'),
    url(r'changeVariables', varActionView.changeVariables, name='changeVariables'),
]
