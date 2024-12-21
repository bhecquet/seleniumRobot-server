

from django.urls import re_path

from variableServer.views import apiView
from variableServer.views import var_action_view
from variableServer.views.apiView import VariableList


urlpatterns = [
    re_path(r'^api/variable/(?P<pk>[0-9]+)/$', VariableList.as_view(), name='variableApiPut'),
    re_path(r'^api/variable', VariableList.as_view(), name='variableApi'),
    re_path(r'^api', apiView.Ping.as_view(), name='variablePing'),
    
    re_path(r'copyVariables', var_action_view.copy_variables, name='copy_variables'),
    re_path(r'changeVariables', var_action_view.change_variables, name='change_variables'),
]
