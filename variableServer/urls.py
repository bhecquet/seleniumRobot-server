
from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers
from variableServer.views import varActionView, apiView
from variableServer.views.apiView import VariableList
from rest_framework.authtoken import views

urlpatterns = [
    url(r'^api/variable/(?P<pk>[0-9]+)/$', VariableList.as_view(), name='variableApiPut'),
    url(r'^api/variable', VariableList.as_view(), name='variableApi'),
    url(r'^api', apiView.Ping.as_view(), name='variablePing'),
    
    url(r'copyVariables', varActionView.copyVariables, name='copyVariables'),
    url(r'changeVariables', varActionView.changeVariables, name='changeVariables'),
]
