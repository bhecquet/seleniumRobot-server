"""seleniumRobotServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers

from snapshotServer import viewsets
from snapshotServer.views.ApplicationVersionListView import ApplicationVersionListView
from snapshotServer.views.ExcludeZoneListView import ExclusionZoneListView
from snapshotServer.views.FileUploadView import FileUploadView
from snapshotServer.views.PictureView import PictureView
from snapshotServer.views.RecomputeDiffView import RecomputeDiffView
from snapshotServer.views.SessionListView import SessionListView
from snapshotServer.views.StepListView import StepListView
from snapshotServer.views.TestListView import TestListView
from snapshotServer.views.TestStatusView import TestStatusView
from snapshotServer.views.TestResultTableView import TestResultTableView
from snapshotServer.views.TestResultView import TestResultView

from commonsServer.views.viewsets import ApplicationViewSet
from django.views.decorators.clickjacking import xframe_options_exempt

router = routers.DefaultRouter()
router.register(r'snapshot', viewsets.SnapshotViewSet)
router.register(r'application', ApplicationViewSet)
router.register(r'testcaseinsession', viewsets.TestCaseInSessionViewSet)
router.register(r'teststep', viewsets.TestStepViewSet)
router.register(r'stepresult', viewsets.StepResultViewSet)
router.register(r'exclude', viewsets.ExcludeZoneViewSet)
router.register(r'session', viewsets.TestSessionViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls), name='api'),
    url(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view(), name='upload'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    url(r'^$', ApplicationVersionListView.as_view(), name='home'),
    
    url(r'^testResults/(?P<version_id>[0-9]+)/$', TestResultTableView.as_view(), name='testResultTableView'),
    url(r'^testResults/result/(?P<testCaseInSessionId>[0-9]+)/$', TestResultView.as_view(), name='testResultView'),

    url(r'^compare/(?P<version_id>[0-9]+)/$', SessionListView.as_view(), name='sessionListView'),
    url(r'^compare/compute/([0-9]+)/$', RecomputeDiffView.as_view(), name='recompute'),
    url(r'^compare/testList/(?P<sessionId>[0-9]+)/$', TestListView.as_view(), name="testlistView"),  
    url(r'^compare/stepList/(?P<testCaseInSessionId>[0-9]+)/$', xframe_options_exempt(StepListView.as_view()), name="steplistView"), 
    url(r'^compare/picture/(?P<testCaseInSessionId>[0-9]+)/(?P<testStepId>[0-9]+)/$', PictureView.as_view(), name="pictureView"), 
    url(r'^compare/excludeList/(?P<snapshotId>[0-9]+)/$', ExclusionZoneListView.as_view(), name="excludeListView"),
    
    # get status of test session or test step
    url(r'^status/(?P<testCaseId>[0-9]+)/$', TestStatusView.as_view(), name="testStatusView"), 
    url(r'^status/(?P<testCaseId>[0-9]+)/(?P<testStepId>[0-9]+)/$', TestStatusView.as_view(), name="testStepStatusView"), 
    
]
