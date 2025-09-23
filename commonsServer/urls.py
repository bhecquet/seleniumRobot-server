
from django.urls import re_path
from commonsServer.views.viewsets import ApplicationViewSet, VersionViewSet,\
    TestEnvironmentViewSet, TestCaseViewSet



urlpatterns = [
    # DEPRECATED. Only for compatibility
    re_path(r'^api/gapplication', ApplicationViewSet.as_view(), name='applicationApi'),
    re_path(r'^api/gversion', VersionViewSet.as_view(), name='versionApi'),
    re_path(r'^api/genvironment', TestEnvironmentViewSet.as_view(), name='environmentApi'),
    re_path(r'^api/gtestcase', TestCaseViewSet.as_view(), name='testCaseApi'),
    
    re_path(r'^api/application', ApplicationViewSet.as_view(), name='application'),
    re_path(r'^api/version', VersionViewSet.as_view(), name='version'),
    re_path(r'^api/environment', TestEnvironmentViewSet.as_view(), name='environment'),
    re_path(r'^api/testcase', TestCaseViewSet.as_view(), name='testcase'),
]

