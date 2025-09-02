from django.conf.urls import include
from rest_framework import routers

from snapshotServer import viewsets
from snapshotServer.views.exclude_zone_list_view import ExclusionZoneListView
from snapshotServer.views.file_upload_view import FileUploadView
from snapshotServer.views.picture_view import PictureView
from snapshotServer.views.recompute_diff_view import RecomputeDiffView
from snapshotServer.views.test_status_view import TestStatusView
from snapshotServer.views.test_result_view import TestResultView
from snapshotServer.views.field_detector_view import FieldDetectorView

from django.urls.conf import re_path, path
from snapshotServer.views.step_reference_view import StepReferenceView
from snapshotServer.views.test_session_summary_view import TestSessionSummaryView

router = routers.DefaultRouter()
router.register(r'testcaseinsession', viewsets.TestCaseInSessionViewSet)
router.register(r'testinfo', viewsets.TestInfoSessionViewSet)
router.register(r'teststep', viewsets.TestStepViewSet)
router.register(r'stepresult', viewsets.StepResultViewSet)
router.register(r'exclude', viewsets.ExcludeZoneViewSet)
# curl -X POST http://localhost:8000/snapshot/api/file/ -F "file=@D:\Dev\seleniumRobot\seleniumRobot-jenkins\covea.pic.jenkins.tests.selenium\jenkins\test-output\loginInvalid\screenshots\login_screen-b7c449.png " -F "stepResult=486"
router.register(r'file', viewsets.FileViewSet)
router.register(r'logs', viewsets.ExecutionLogsViewSet)

urlpatterns = [
    re_path(r'^api/', include(router.urls), name='api'),
    
    re_path(r'^api/session', viewsets.TestSessionViewSet.as_view(), name='session'),
    
    re_path(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view(), name='upload'),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # image-field-detector
    re_path(r'^detect/$', FieldDetectorView.as_view(), name="detect"),
    
    path(r'stepReference/<int:step_result_id>/', StepReferenceView.as_view(), name='stepReference'),
    re_path(r'^stepReference/$', StepReferenceView.as_view(), name='uploadStepRef'),
    
    re_path(r'^testResults/result/(?P<test_case_in_session_id>[0-9]+)/$', TestResultView.as_view(), name='testResultView'),
    re_path(r'^testResults/summary/(?P<sessionId>[0-9]+)/$', TestSessionSummaryView.as_view(), name='testSessionSummaryView'),

    re_path(r'^compare/compute/(?P<snapshot_id>[0-9]+)/$', RecomputeDiffView.as_view(), name='recompute'),
    # force view to set CSRF cookie so that editing exclusion zones do not fail  
    re_path(r'^compare/picture/(?P<test_case_in_session_id>[0-9]+)/(?P<test_step_id>[0-9]+)/$', PictureView.as_view(), name="pictureView"), 
    re_path(r'^compare/picture/(?P<test_case_in_session_id>[0-9]+)/(?P<test_step_id>[0-9]+)/noheader/$', PictureView.as_view(), name="pictureViewNoHeader"), 
    re_path(r'^compare/excludeList/(?P<ref_snapshot_id>None|[0-9]+)/(?P<step_snapshot_id>[0-9]+)/$', ExclusionZoneListView.as_view(), name="excludeListView"),
    
    # get status of test session or test step
    re_path(r'^status/(?P<testCaseId>[0-9]+)/$', TestStatusView.as_view(), name="testStatusView"), 
    re_path(r'^status/(?P<testCaseId>[0-9]+)/(?P<testStepId>[0-9]+)/$', TestStatusView.as_view(), name="testStepStatusView"), 

    
]
