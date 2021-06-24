
from django.conf.urls import url, include
from django.urls import re_path
from rest_framework import routers
from commonsServer.views.api.VersionView import VersionView
from commonsServer.views.api.ApplicationView import ApplicationView
from commonsServer.views.api.EnvironmentView import EnvironmentView
from commonsServer.views.api.TestCaseView import TestCaseView
from commonsServer.views import viewsets


router = routers.DefaultRouter()
router.register(r'application', viewsets.ApplicationViewSet)
router.register(r'version', viewsets.VersionViewSet)
router.register(r'testcase', viewsets.TestCaseViewSet) 
router.register(r'environment', viewsets.TestEnvironmentViewSet)

urlpatterns = [
    re_path(r'^api/', include(router.urls), name='api'),
    re_path(r'^api/gapplication', ApplicationView.as_view(), name='applicationApi'),
    re_path(r'^api/gversion', VersionView.as_view(), name='versionApi'),
    re_path(r'^api/genvironment', EnvironmentView.as_view(), name='environmentApi'),
    re_path(r'^api/gtestcase', TestCaseView.as_view(), name='testCaseApi'),
]
