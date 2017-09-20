
from django.conf.urls import url, include
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
    url(r'^api/', include(router.urls), name='api'),
    url(r'^api/gapplication', ApplicationView.as_view(), name='applicationApi'),
    url(r'^api/gversion', VersionView.as_view(), name='versionApi'),
    url(r'^api/genvironment', EnvironmentView.as_view(), name='environmentApi'),
    url(r'^api/gtestcase', TestCaseView.as_view(), name='testCaseApi'),
]
