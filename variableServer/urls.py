

from django.urls import re_path

from variableServer.views import api_view
from variableServer.views import var_action_view
from variableServer.views.api_view import VariableList

urlpatterns = [
    re_path(r'^api/variable/(?P<var_id>[0-9]+)/file$', api_view.VariableDownload.as_view({'get':'get'}), name='download_variable'),
    re_path(r'^api/variable/(?P<pk>[0-9]+)/$', VariableList.as_view({'patch': 'patch', 'delete': 'delete'}), name='variableApiPut'),
    re_path(r'^api/variable', VariableList.as_view({'get': 'get', 'post': 'post'}), name='variableApi'),
    re_path(r'^api', api_view.Ping.as_view(), name='variablePing'),
    re_path(r'copyVariables', var_action_view.copy_variables, name='copy_variables'),
    re_path(r'changeVariables', var_action_view.change_variables, name='change_variables'),
]
