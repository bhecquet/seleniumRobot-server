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
from snapshotServer.views.FieldDetectorView import FieldDetectorView

from commonsServer.views.viewsets import ApplicationViewSet
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.urls.conf import re_path, path
from snapshotServer.views.StepReferenceView import StepReferenceView

router = routers.DefaultRouter()
router.register(r'snapshot', viewsets.SnapshotViewSet)
router.register(r'application', ApplicationViewSet)
router.register(r'testcaseinsession', viewsets.TestCaseInSessionViewSet)
router.register(r'teststep', viewsets.TestStepViewSet)
router.register(r'stepresult', viewsets.StepResultViewSet)
router.register(r'exclude', viewsets.ExcludeZoneViewSet)
router.register(r'session', viewsets.TestSessionViewSet)

urlpatterns = [
    re_path(r'^api/', include(router.urls), name='api'),
    re_path(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view(), name='upload'),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # image-field-detector
    re_path(r'^detect/$', FieldDetectorView.as_view(), name="detect"),

    re_path(r'^$', ApplicationVersionListView.as_view(), name='home'),
    
    path(r'stepReference/<int:step_result_id>/', StepReferenceView.as_view(), name='stepReference'),
    re_path(r'^stepReference/$', StepReferenceView.as_view(), name='uploadStepRef'),
    
    re_path(r'^testResults/(?P<version_id>[0-9]+)/$', TestResultTableView.as_view(), name='testResultTableView'),
    re_path(r'^testResults/result/(?P<testCaseInSessionId>[0-9]+)/$', TestResultView.as_view(), name='testResultView'),

    re_path(r'^compare/(?P<version_id>[0-9]+)/$', SessionListView.as_view(), name='sessionListView'),
    re_path(r'^compare/compute/([0-9]+)/$', RecomputeDiffView.as_view(), name='recompute'),
    re_path(r'^compare/testList/(?P<sessionId>[0-9]+)/$', TestListView.as_view(), name="testlistView"),  
    # force view to set CSRF cookie so that editing exclusion zones do not fail 
    re_path(r'^compare/stepList/(?P<testCaseInSessionId>[0-9]+)/$', csrf_exempt(ensure_csrf_cookie(xframe_options_exempt(StepListView.as_view()))), name="steplistView"), 
    re_path(r'^compare/picture/(?P<testCaseInSessionId>[0-9]+)/(?P<testStepId>[0-9]+)/$', PictureView.as_view(), name="pictureView"), 
    re_path(r'^compare/excludeList/(?P<ref_snapshot_id>[0-9]+)/(?P<step_snapshot_id>[0-9]+)/$', ExclusionZoneListView.as_view(), name="excludeListView"),
    
    # get status of test session or test step
    re_path(r'^status/(?P<testCaseId>[0-9]+)/$', TestStatusView.as_view(), name="testStatusView"), 
    re_path(r'^status/(?P<testCaseId>[0-9]+)/(?P<testStepId>[0-9]+)/$', TestStatusView.as_view(), name="testStepStatusView"), 

    
]
