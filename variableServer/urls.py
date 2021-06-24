

from django.urls import re_path

from variableServer.views import varActionView, apiView
from variableServer.views.apiView import VariableList


urlpatterns = [
    re_path(r'^api/variable/(?P<pk>[0-9]+)/$', VariableList.as_view(), name='variableApiPut'),
    re_path(r'^api/variable', VariableList.as_view(), name='variableApi'),
    re_path(r'^api', apiView.Ping.as_view(), name='variablePing'),
    
    re_path(r'copyVariables', varActionView.copyVariables, name='copyVariables'),
    re_path(r'changeVariables', varActionView.changeVariables, name='changeVariables'),
]
