'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse

from snapshotServer.models import StepResult, Snapshot, TestSession,\
    TestCaseInSession
from django.conf import settings
from snapshotServer.tests import SnapshotTestCase,\
    authenticate_test_client_for_web_view
import os
from django.test.client import Client
import json

class TestTestResultView(SnapshotTestCase):

    fixtures = ['testresult_commons.yaml', 'testresult_ok.yaml', 'testresult_ko.yaml', 'test_result_snapshot_comparison.yaml']
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        authenticate_test_client_for_web_view(self.client)
           
    def test_report_result_ok(self):
        """
        Test that step results are returned for our test
        """
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(len(response.context['object_list']), 4)
        
        # check order of steps
        self.assertEqual(list(response.context['object_list'])[0], StepResult.objects.get(pk=1))
        self.assertEqual(list(response.context['object_list'])[1], StepResult.objects.get(pk=2))
        self.assertEqual(list(response.context['object_list'])[2], StepResult.objects.get(pk=3))
        self.assertEqual(list(response.context['object_list'])[3], StepResult.objects.get(pk=4))
        self.assertEqual(response.context['currentTest'].id, 1)
        self.assertEqual(response.context['testCaseId'], "1")
        self.assertIsNone(response.context['snasphotComparisonResult']) # no snapshots to compare
        self.assertEqual(response.context['status'], "SUCCESS")
        self.assertEqual(response.context['browserOrApp'], "Firefox")
        self.assertEqual(response.context['applicationType'], "Browser")
        self.assertEqual(response.context['stacktrace'], [''])
        self.assertEqual(response.context['logs'], [' INFO  2023-10-25 14:53:50,941 [TestNG-test=jenkins-1] SeleniumRobotTestListener: Start method loginInvalid\r', 
                                                    'INFO  2023-10-25 14:54:50,941 [TestNG-test=jenkins-1] SeleniumRobotTestListener: Finished method loginInvalid'])
        self.assertEqual(response.context['lastStepDetails'], json.loads(StepResult.objects.get(pk=4).stacktrace))
        
        # check content
        html = self.remove_spaces(response.rendered_content)
        
        ## details table
        self.assertTrue("""<table class="table table-bordered table-sm"><tr><th>Application type</th><td>Browser</td></tr><tr><th>Application</th><td>Firefox</td></tr><tr><th>Grid node</th><td>None</td></tr>""" in html)
        ## links to last state
        self.assertTrue('<th>Issue</th><td><a href="https://jiraserver/PROJECT/PRO-1">Issue</a></td></tr>'
        "<tr><th>Some information</th><td>some text</td></tr>"
        '<tr><th>Last State</th><td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a>'
        '<a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a>' in html)
        ## steps / sub-steps
        self.assertTrue("""<div class="box collapsed-box success"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button><span class="step-title">openPage with args: (https://jenkins/jenkins/, )  - 0.7 secs</span><span><i class="fas fa-file-video"></i>0.005 s</span>""" in html) 
        self.assertTrue("""<div class="message-conf"><span class="stepTimestamp mr-1">14:53:58.815</span>Opening page LoginPage""" in html)
        self.assertTrue("""<div class="message-conf"><span class="stepTimestamp mr-1">14:53:58.816</span>setWindowToRequestedSize on on page LoginPage""" in html)
        self.assertTrue("""<div class="message-conf"><span class="stepTimestamp mr-1">14:53:58.816</span>maximizeWindow on on page LoginPage""" in html)
        self.assertTrue("""<div class="box collapsed-box success"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button><span class="step-title">loginInvalid with args: (foo, bar, )  - 2.0 secs</span><span><i class="fas fa-file-video"></i>1.171 s</span>""" in html) 
        ### sub-step inside step
        self.assertTrue("""<ul><li><div class="message-conf"><span class="stepTimestamp mr-1">14:54:01.41</span>click on ButtonElement check, by={By.name: check}""" in html)
        self.assertTrue('<div class="box collapsed-box success"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse">'
                        '<i class="fa fa-plus"></i></button><span class="step-title">getErrorMessage   - 5.0 secs</span><span><i class="fas fa-file-video"></i>3.508 s</span>' in html) 
        self.assertTrue("""<div class="box collapsed-box success"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button><span class="step-title">Test end  - 0.2 secs</span><span><i class="fas fa-file-video"></i>9.2 s</span>""" in html) 
        ## pictures on steps
        self.assertTrue('''<a href="#" onclick="$('#imagepreview').attr('src', $('#88').attr('src'));$('#imagemodal').modal('show');"><img id="88" src="/snapshot/api/file/88/download/" style="width: 300px"></a></div></div><div class="text-center">drv:main:Current Window: S&#x27;identifier [Jenkins]</div>'''
                        '<div class="text-center font-weight-lighter"><a href="https://jenkins/login?from=%2Fjenkins%2F" target=url>URL</a>' in html) 
        ## log value on step
        self.assertTrue('<table class="table table-bordered table-sm"><tr><th width="15%">Key</th><th width="60%">Message</th><th width="25%">Value</th></tr>'
                        '<tr><td><div class="message-conf"><span class="stepTimestamp mr-1"></span>key' in html)
        ## snapshot comparison is not displayed
        self.assertFalse('Snapshot comparison' in html)
        ## files available
        self.assertTrue("""Video capture:<a href="/snapshot/api/file/91/download/">file</a>""" in html)
        self.assertTrue("""Network capture "main" browser:<a href="/snapshot/api/file/92/download/">HAR file</a>""" in html)
        ## no description in details table
        self.assertFalse("""<th>Description</th>""" in html)
        self.assertFalse("""<th>Started by</th>""" in html)
        
    def test_report_result_ko(self):
        """
        Check when step is KO
        . last step in red
        . failed step in red
        . error message displayed
        . reference picture is displayed
        """
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 11}))
        self.assertEqual(len(response.context['object_list']), 4)
        self.assertEqual(response.context['status'], "FAILURE")
        
        html = self.remove_spaces(response.rendered_content)

        # a step in error has the right class
        self.assertTrue('<div class="box collapsed-box failed"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse">'
                        '<i class="fa fa-plus"></i></button><span class="step-title">getErrorMessage&lt;&gt;   - 5.0 secs</span><span><i class="fas fa-file-video"></i>4.35 s</span>' in html)
        self.assertTrue('<div class="box collapsed-box failed"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse">'
                        '<i class="fa fa-plus"></i></button><span class="step-title">Test end  - 0.2 secs</span><span><i class="fas fa-file-video"></i>10.519 s</span>' in html)
         
        # error message
        ## in header
        self.assertTrue('<tr><th>Last State</th><td><a class="errorTooltip"><i class="fas fa-file-alt" aria-hidden="true" data-toggle="popover" title="Exception" data-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"></i></a></td></tr>' in html)
        ## on last step
        self.assertTrue('<div class="message-log message-conf"><span class="stepTimestamp mr-1"></span>Test is KO with error: class java.lang.AssertionError: expected [false] but &lt;&gt; found [true]' in html)
        ## error message on step
        self.assertTrue("""<div class="message-error message-conf"><span class="stepTimestamp mr-1"></span>!!!FAILURE ALERT!!! - Assertion Failure: expected [false] but found [true]""" in html)
        
        # reference snapshot
        self.assertTrue('''<div class="message-snapshot col"><div class="message-snapshot col"><div class="text-center"><a href="#" onclick="$('#imagepreview').attr('src', $('#108').attr('src'));$('#imagemodal').modal('show');">'''
                        '<img id="108" src="/snapshot/api/file/108/download/" style="width: 300px"></a></div></div><div class="text-center">Step beginning state</div>' in html)
        self.assertTrue('''<div class="message-snapshot col"><div class="message-snapshot col"><div class="text-center"><a href="#" onclick="$('#imagepreview').attr('src', $('#109').attr('src'));$('#imagemodal').modal('show');">'''
                        '<img id="109" src="/snapshot/api/file/109/download/" style="width: 300px"></a></div></div><div class="text-center">Valid-reference</div>' in html)
         
    def test_report_result_encoding(self):
        """
        Check errors / messages / assertions are encoded
        """
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 11}))
        self.assertEqual(len(response.context['object_list']), 4)
        self.assertEqual(response.context['status'], "FAILURE")
        
        html = self.remove_spaces(response.rendered_content)
        
        # step is encoded
        self.assertTrue("""<span class="step-title"> getErrorMessage&lt;&gt;""")
        
        # error message is encoded
        self.assertTrue("""<div class="message-error">class java.lang.AssertionError: expected [false] but &lt;_&gt; found [true]</div>""" in html)
        
        # actions are encoded
        self.assertTrue("""<span class="stepTimestamp mr-1"></span>Test is KO with error: class java.lang.AssertionError: expected [false] but &lt;&gt; found [true]""" in html)
        
        # logs are encoded
        self.assertTrue("""<div>INFO  2023-10-25 14:53:50,941 [TestNG-test=jenkins-1] SeleniumRobotTestListener: Start method loginInvalid &lt;;&gt;""" in html)
        
        # last state is encoded
        self.assertTrue("""data-toggle="popover" title="Exception" data-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;""" in html)
        
    def test_report_with_snapshot_comparison_ok_display_only(self):
        """
        Test the case where snapshot comparison is active, but comparison behaviour is 'DISPLAY_ONLY'
        . an additional step giving snapshot comparison result should be present 
        """
        step_snapshot = Snapshot.objects.get(pk=2)
        step_snapshot.stepResult = StepResult.objects.get(pk=2)
        step_snapshot.save()
        
        session = TestSession.objects.get(pk=1)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'DISPLAY_ONLY'
        session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['status'], "SUCCESS")
        
        html = self.remove_spaces(response.rendered_content)
        self.assertTrue('<div class="box collapsed-box success"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button>Snapshot comparison' in html)
        self.assertTrue('<i class="fas fa-file-video"></i>1.171 s<i class="fa-solid fa-code-compare font-success"></i>' in html) # check icon is present when comparison is done in step
        self.assertEqual(html.count('fa-solid fa-code-compare'), 1, "Only one icon of image comparison should be present")
        self.assertTrue('Snapshot comparison OK' in html)
        
    def test_report_with_snapshot_comparison_ko_display_only(self):
        """
        Test the case where snapshot comparison is active, but comparison behaviour is 'DISPLAY_ONLY'
        Even if comparison is KO, result should not be modified
        """
        step_snapshot = Snapshot.objects.get(pk=3)
        step_snapshot.stepResult = StepResult.objects.get(pk=2)
        step_snapshot.save()
        
        session = TestSession.objects.get(pk=1)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'DISPLAY_ONLY'
        session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['status'], "SUCCESS")
        
        html = self.remove_spaces(response.rendered_content)
        
        # result is OK, but snapshot comparison step is KO
        self.assertTrue('<div class="box collapsed-box failed"><div class="box-header with-border">'
                        '<button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button>Snapshot comparison' in html)
        self.assertTrue('<i class="fas fa-file-video"></i>1.171 s<i class="fa-solid fa-code-compare font-failed"></i>' in html) # check icon is present when comparison is done in step
        self.assertEqual(html.count('fa-solid fa-code-compare'), 1, "Only one icon of image comparison should be present")
        self.assertTrue('Snapshot comparison KO' in html)
         
        
    def test_report_with_snapshot_comparison_ko_change_test_result(self):
        """
        Test the case where snapshot comparison is active, but comparison behaviour is 'CHANGE_TEST_RESULT'
        Comparison is KO, result should be modified
        """
        step_snapshot = Snapshot.objects.get(pk=3)
        step_snapshot.stepResult = StepResult.objects.get(pk=2)
        step_snapshot.save()
        
        session = TestSession.objects.get(pk=1)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'CHANGE_TEST_RESULT'
        session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['status'], "FAILURE")
        
        html = self.remove_spaces(response.rendered_content)
        self.assertTrue('<div class="box collapsed-box failed"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button>Snapshot comparison' in html)
        self.assertTrue('Snapshot comparison KO' in html)
         
    def test_report_with_snapshot_comparison_error_change_test_result(self):
        """
        Test the case where snapshot comparison is active, but comparison behaviour is 'CHANGE_TEST_RESULT'
        Comparison is in error, result should not be modified
        """
        step_snapshot = Snapshot.objects.get(pk=4)
        step_snapshot.stepResult = StepResult.objects.get(pk=2)
        step_snapshot.save()
        
        session = TestSession.objects.get(pk=1)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'CHANGE_TEST_RESULT'
        session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['status'], "SUCCESS")

        html = self.remove_spaces(response.rendered_content)
        # no snapshot comparison step should be present as there was an error
        self.assertFalse('Snapshot comparison' in html)
        
    def test_report_with_grid_node(self):
        """
        Check that when grid node information is available, it's displayed
        """
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.gridNode = "mynode.domain.com"
        test_case_in_session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        html = self.remove_spaces(response.rendered_content)
        
        # details table
        self.assertTrue("""<table class="table table-bordered table-sm"><tr><th>Application type</th><td>Browser</td></tr><tr><th>Application</th><td>Firefox</td></tr><tr><th>Grid node</th><td>mynode.domain.com</td></tr>""" in html)
        
    def test_report_with_step_in_warning(self):
        """
        Check that if a step is in warning, it has the right color
        """
        test_case_in_session = TestCaseInSession.objects.get(pk=11)
        test_case_in_session.testSteps.set([11, 12, 15, 14])
        test_case_in_session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 11}))
        html = self.remove_spaces(response.rendered_content)

        self.assertTrue("""<div class="box collapsed-box warning"><div class="box-header with-border"><button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-plus"></i></button><span class="step-title">getErrorMessage warn  - 5.0 secs</span><span><i class="fas fa-file-video"></i>4.35 s</span>""" in html)
    
    def test_report_with_description(self):
        """
        Check test description is displayed, and special characters are escaped
        """
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.description = """Some extra test
<param1> <param2>
;&nbsp;"""
        test_case_in_session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        html = self.remove_spaces(response.rendered_content)

        self.assertTrue("""<th>Description</th><td>Some extra test""" in html)
        self.assertTrue("""&lt;param1&gt; &lt;param2&gt;""" in html)
        self.assertTrue(""";&amp;nbsp;</td>""" in html)
        
        
    def test_report_with_started_by(self):
        """
        Check "started by" is displayed
        """
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.session.startedBy = """http://myTestLauncher/foo/bar?test=test1&param=1"""
        test_case_in_session.session.save()
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 1}))
        html = self.remove_spaces(response.rendered_content)

        self.assertTrue("""<tr><th>Started by</th><td><a href=http://myTestLauncher/foo/bar?test=test1&amp;param=1>http://myTestLauncher/foo/bar?test=test1&amp;param=1</a></td></tr>""" in html)

                 
    def test_report_message_style(self):
        """
        Check style of message is set (success, error, warning, ...)
        """
        
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 11}))
        self.assertEqual(len(response.context['object_list']), 4)
        self.assertEqual(response.context['status'], "FAILURE")
        
        html = self.remove_spaces(response.rendered_content)

        # messages
        self.assertTrue('<div class="message-log message-conf"><span class="stepTimestamp mr-1"></span>Test is KO with error: class java.lang.AssertionError: expected [false] but &lt;&gt; found [true]' in html)
        self.assertTrue("""<div class="message-error message-conf"><span class="stepTimestamp mr-1"></span>!!!FAILURE ALERT!!! - Assertion Failure: expected [false] but found [true]""" in html)
        self.assertTrue("""<div class="message-warning message-conf"><span class="stepTimestamp mr-1"></span>[NOT RETRYING] max retry count (0) reached""" in html)
        self.assertTrue("""<div class="message-info message-conf"><span class="stepTimestamp mr-1"></span>Video file copied to videoCapture.avi""" in html)
 
         
    def test_stacktraceExists(self):
        """
        Test that step results are returned for our test
        """
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 11}))
        self.assertEqual(len(response.context['object_list']), 4)
        self.assertEqual(len(response.context['stacktrace']), 2)
        self.assertTrue('line1' in response.context['stacktrace'][0])


   
# Tests
# - no logs available
# - cannot load step details

# testStepAnnotationWithError
# testStepAnnotationWithErrorNoDetails
# testStepAnnotationNoErrors
# testStepAnnotationNoErrorCause
