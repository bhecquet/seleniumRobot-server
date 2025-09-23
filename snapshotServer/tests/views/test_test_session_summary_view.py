from snapshotServer.tests import SnapshotTestCase,\
    authenticate_test_client_for_web_view_with_permissions
from django.conf import settings
import os
from django.test.client import Client
from django.urls.base import reverse
from snapshotServer.models import StepResult, Snapshot, TestSession,\
    TestCaseInSession, Error
from django.db.models import Q
from django.contrib.auth.models import Permission

from variableServer.models import Application


class TestTestSessionSummaryView(SnapshotTestCase):

    fixtures = ['tests_summary_commons.yaml', 
                'tests_summary_ok.yaml', 
                'tests_summary_ko.yaml', 
                'tests_summary_ko2.yaml', 
                'tests_summary_skipped.yaml', 
                'tests_summary_snapshot_comparison.yaml'
                ]
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    # summary 2 tests 
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        
    def test_summary_report_no_security_not_authenticated(self):
        """
        Check that with security disabled, we  access view without authentication
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            self.assertEqual(200, response.status_code)
        
    def test_summary_report_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
        
        # check we are redirected to login
        self.assertEqual(302, response.status_code)
        self.assertEqual("/accounts/login/?next=/snapshot/testResults/summary/1/", response.url)
        
    def test_summary_report_security_authenticated_no_permission(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot view result => error page displayed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp2')))
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            
            # check we have no permission to view the report
            self.assertEqual(403, response.status_code)
           
        
    def test_summary_report_security_authenticated_with_permission(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can view result
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
            
    def test_summary_report_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 error
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 123}))
            
            # check we have no permission to view the report
            self.assertEqual(404, response.status_code)
           
    def test_summary_report_result_ok(self):
        """
        Check that the test is displayed in summary
        - last state image is available
        - link to individual test is ok
        - no badge or related error is displayed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))

            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            
            self.assertEqual(1, response.context['testSession'].id)
            self.assertEqual(['Issue', 'Some information', 'Last State'], response.context['testInfoList'])
            self.assertEquals(1, test_case_in_session.id)
            self.assertIsNone(test_case_info[0]) # no snapshot comparison done
            self.assertEquals(4, test_case_info[1]) # number of steps
            self.assertEquals(0, test_case_info[2]) # number of failed steps
            self.assertEquals(7, test_case_info[3]) # test duration
            self.assertEquals([], test_case_info[4]) # tests with the same error (none as test is OK
            self.assertEquals({'id': -1, 'error_short': '', 'error': '', 'color': 'white'}, test_case_info[5]) # badge information => no content
            self.assertEquals({'Issue': {'type': 'hyperlink', 'link': 'https://jiraserver/PROJECT/PRO-1', 'info': 'Issue'}, 'Some information': {'type': 'string', 'info': 'some text'}, 'Last State': {'type': 'multipleinfo', 'infos': [{'link': 'loginInvalid_3-1_Test_end--9a514b.png', 'id': 90, 'type': 'imagelink', 'info': 'Image'}, {'link': 'videoCapture.avi', 'id': 91, 'type': 'videolink', 'info': 'Video'}]}}, test_case_info[6]) # test duration
            
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # shortcut to image / video present
            self.assertTrue("""<td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
            # link to detailed result
            self.assertTrue("""<tr class="testSuccess"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/1/' info="ok" data-bs-toggle="tooltip" title="no description available">testJenkins</a>""" in html)
            # step count +  duration + no related errors
            self.assertTrue("""<td name="stepsTotal-1">4</td><td name="relatedErrors-1"></td><td>7 sec.</td>""" in html)
            # additional test information
            self.assertTrue("""<td><a href="https://jiraserver/PROJECT/PRO-1">Issue</a></td><td>some text</td>""" in html)
            # badge not displayed when test is OK
            self.assertTrue("""title="no description available">testJenkins</a><span class="badge bg-primary" style="background-color: white !important" data-bs-toggle="tooltip" title=""></span></td><td name="stepsTotal-1">""" in html)
        
           
    def test_summary_report_contains_multiple_tests(self):
        """
        Check that multiple tests can be displayed in the report
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            # add an other result is Session 1
            tcis = TestCaseInSession.objects.get(pk=11)
            session = TestSession.objects.get(pk=1)
            tcis.session = session
            tcis.save()
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            self.assertEqual(2, len(response.context['object_list']))
    
            self.assertEqual(1, response.context['testSession'].id)
            self.assertEqual(['Issue', 'Some information', 'Last State'], response.context['testInfoList'])
            
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # shortcut to image / video present
            self.assertTrue("""<td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
            # link to detailed result
            self.assertTrue("""<tr class="testSuccess"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/1/' info="ok" data-bs-toggle="tooltip" title="no description available">testJenkins</a>""" in html)
            # no badge as test is OK
            self.assertTrue("""testJenkins</a><span class="badge bg-primary" style="background-color: white !important" data-bs-toggle="tooltip" title=""></span></td>""" in html)
            # step count +  duration
            self.assertTrue("""<td name="stepsTotal-2">4</td><td name="relatedErrors-2"></td><td>7 sec.</td>""" in html)
            # additional test information
            self.assertTrue("""<td>7 sec.</td><td><a href="https://jiraserver/PROJECT/PRO-1">Issue</a></td><td>some text</td><td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
            
            # test KO is also present
            self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/11/' info="ko" data-bs-toggle="tooltip" title="no description available">testJenkinsKo</a>""" in html)
            # badge not visible as error has not been recorded for this test
            self.assertTrue("""testJenkinsKo</a><span class="badge bg-primary" style="background-color: white !important" data-bs-toggle="tooltip" title=""></span></td>""" in html)
            # information are in the right cell
            self.assertTrue("""<td>12 sec.</td><td></td><td></td><td><a class="errorTooltip" tabindex="0" data-bs-trigger="focus" data-bs-toggle="popover" title="Exception" data-bs-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"><i class="fas fa-file-alt" aria-hidden="true"></i></a></td></tr>""" in html)
              
            # chek test order depends on date
            self.assertTrue(html.find(">testJenkinsKo<") < html.find(">testJenkins<"))
               
    def test_summary_report_result_ok_with_snapshot_comparison_ok(self):
        """
        Check that the icon for snapshot comparison is present
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            step_snapshot = Snapshot.objects.get(pk=2)
            step_snapshot.stepResult = StepResult.objects.get(pk=2)
            step_snapshot.save()
            
            session = TestSession.objects.get(pk=1)
            session.compareSnapshot = True
            session.compareSnapshotBehaviour = 'DISPLAY_ONLY'
            session.save()
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            self.assertEqual(1, len(response.context['object_list']))
    
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # snapshot comparison icon is present
            self.assertTrue("""<i class="fa-solid fa-code-compare font-success" data-bs-toggle="tooltip" title="snapshot comparison successful"></i><a href='/snapshot/testResults/result/1/' info="ok" data-bs-toggle="tooltip" title="no description available">testJenkins</a>""" in html)

        
    def test_summary_report_result_ok_with_snapshot_comparison_ko(self):
        """
        Check that the icon for snapshot comparison is present and red
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
            
            step_snapshot = Snapshot.objects.get(pk=2)
            step_snapshot.stepResult = StepResult.objects.get(pk=2)
            step_snapshot.tooManyDiffs = True
            step_snapshot.save()
            
            session = TestSession.objects.get(pk=1)
            session.compareSnapshot = True
            session.compareSnapshotBehaviour = 'DISPLAY_ONLY'
            session.save()
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 1}))
            self.assertEqual(1, len(response.context['object_list']))
            
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            self.assertEquals(1, test_case_in_session.id)
            self.assertFalse(test_case_info[0]) # snapshot comparison is KO
            self.assertEquals(4, test_case_info[1]) # number of steps
            self.assertEquals(0, test_case_info[2]) # number of failed steps
            self.assertEquals(7, test_case_info[3]) # test duration
    
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # snapshot comparison icon is present
            self.assertTrue("""<i class="fa-solid fa-code-compare font-failed" data-bs-toggle="tooltip" title="snapshot comparison failed"></i><a href='/snapshot/testResults/result/1/' info="ok" data-bs-toggle="tooltip" title="no description available">testJenkins</a>""" in html)

    def test_summary_report_result_ko(self):
        """
        Check that the test is displayed in summary
        - link to individual test is ok
        - number of failed steps is ok
        - no badge as no error instance is recorded for this test (this may happen when test fails immediately without executing any step
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 11}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEqual(['Last State'], response.context['testInfoList'])
            self.assertEquals(11, test_case_in_session.id)
            self.assertIsNone(test_case_info[0]) # no snapshot comparison done
            self.assertEquals(5, test_case_info[1]) # number of steps
            self.assertEquals(3, test_case_info[2]) # number of failed steps
            self.assertEquals(12, test_case_info[3]) # test duration
            self.assertEquals([], test_case_info[4]) # tests with the same error (none as test has no error recorded)
            self.assertEquals({'id': -1, 'error_short': '', 'error': '', 'color': 'white'}, test_case_info[5]) # badge information => no content
            self.assertEquals({'Last State': {'type': 'multipleinfo', 'infos': [{'type': 'log', 'info': 'Browsermob proxy (captureNetwork option) is only compatible with DIRECT and <MANUAL>'}]}}, test_case_info[6]) # test info
     
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # test is KO
            self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/11/' info="ko" data-bs-toggle="tooltip" title="no description available">testJenkinsKo</a>""" in html)
             
            # error message displayed
            self.assertTrue("""<a class="errorTooltip" tabindex="0" data-bs-trigger="focus" data-bs-toggle="popover" title="Exception" data-bs-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"><i class="fas fa-file-alt" aria-hidden="true"></i></a></td>""" in html)
        

    def test_summary_report_result_multiple_steps_ko(self):
        """
        If multiple steps are KO, only the first one is returned
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            # add a seconde failed step
            step_result12 = StepResult.objects.get(id=12)
            step_result12.result = False
            step_result12.save()
            
            error = Error(stepResult=StepResult.objects.get(id=12),
                          action="loginInvalid>sendKeys on Page.user",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in sendKeys")
            error.save()
            
            error = Error(stepResult=StepResult.objects.get(id=13),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error.save()
            
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 11}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
    
            self.assertEquals([], test_case_info[4]) # tests with the same error (none as test has no error recorded)
            self.assertEquals({'id': 0, 'error_short': 'loginInvalid', 'error': 'Error WebDriverException in sendKeys in loginInvalid>sendKeys on Page.user', 'color': 'crimson'}, test_case_info[5]) # Only the first error is kept
       
    def test_summary_report_result_ko_with_recorded_error_no_related(self):
        """
        Same as test_summary_report_result_ko but we record an error for the failed step
        Check
        - a badge is present for the failed test
        - no related error is displayed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            error = Error(stepResult=StepResult.objects.get(id=13),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error.save()
    
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 11}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEqual(['Last State'], response.context['testInfoList'])
            self.assertEquals(11, test_case_in_session.id)
            self.assertIsNone(test_case_info[0]) # no snapshot comparison done
            self.assertEquals(5, test_case_info[1]) # number of steps
            self.assertEquals(3, test_case_info[2]) # number of failed steps
            self.assertEquals(12, test_case_info[3]) # test duration
            self.assertEquals([], test_case_info[4]) # tests with the same error (none as no test has the same error)
            self.assertEquals({'id': 0, 'error_short': 'getErrorMessage<', 'error': 'Error WebDriverException in search in getErrorMessage<> >getText on HtmlElement error message', 'color': 'crimson'}, test_case_info[5]) # badge information => no content
            self.assertEquals({'Last State': {'type': 'multipleinfo', 'infos': [{'type': 'log', 'info': 'Browsermob proxy (captureNetwork option) is only compatible with DIRECT and <MANUAL>'}]}}, test_case_info[6]) # test info
     
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # test is KO
            self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/11/' info="ko" data-bs-toggle="tooltip" title="no description available">testJenkinsKo</a>""" in html)
             
            # error message displayed
            self.assertTrue("""<a class="errorTooltip" tabindex="0" data-bs-trigger="focus" data-bs-toggle="popover" title="Exception" data-bs-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"><i class="fas fa-file-alt" aria-hidden="true"></i></a></td>""" in html)
        
            # badge present and displayed
            self.assertTrue("""title="no description available">testJenkinsKo</a><span class="badge bg-primary" style="background-color: crimson !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&lt;&gt; &gt;getText on HtmlElement error message">getErrorMessage&lt;</span></td><td name="stepsTotal-1">5""" in html)
        
            # no related error displayed
            self.assertTrue("""title="3 step(s) failed">*</a></sup></td><td name="relatedErrors-1"></td><td>12 sec.</td><""" in html)
    
        
    def test_summary_report_result_ko_with_recorded_error_with_related(self):
        """
        Same as test_summary_report_result_ko but we record an error for the failed step
        This time, a related error has also been found
        Check
        - a badge is present for the failed test
        - number of related error is displayed and canvas is accessible
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            # record error for test_case_in_session=11
            error = Error(stepResult=StepResult.objects.get(id=13),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error.save()
            
            # record error for test_case_in_session=110
            error110 = Error(stepResult=StepResult.objects.get(id=130),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error110.save()
            error110.relatedErrors.set([error])
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 110}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            
            self.assertEqual(110, response.context['testSession'].id)
            self.assertEqual(['Last State'], response.context['testInfoList'])
            self.assertEquals(110, test_case_in_session.id)
            self.assertIsNone(test_case_info[0]) # no snapshot comparison done
            self.assertEquals(4, test_case_info[1]) # number of steps
            self.assertEquals(2, test_case_info[2]) # number of failed steps
            self.assertEquals(7, test_case_info[3]) # test duration
            self.assertEquals([TestCaseInSession.objects.get(id=11)], test_case_info[4]) # tests with the same error (the related error is returned)
            self.assertEquals({'id': 0, 'error_short': 'getErrorMessage<', 'error': 'Error WebDriverException in search in getErrorMessage<> >getText on HtmlElement error message', 'color': 'crimson'}, test_case_info[5]) # badge information => information about the error
            self.assertEquals({'Last State': {'type': 'multipleinfo', 'infos': [{'type': 'log', 'info': 'Browsermob proxy (captureNetwork option) is only compatible with DIRECT and <MANUAL>'}]}}, test_case_info[6]) # test info
     
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # test is KO
            self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/110/' info="ko" data-bs-toggle="tooltip" title="no description available">testJenkinsKo2</a>""" in html)
             
            # error message displayed
            self.assertTrue("""<a class="errorTooltip" tabindex="0" data-bs-trigger="focus" data-bs-toggle="popover" title="Exception" data-bs-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"><i class="fas fa-file-alt" aria-hidden="true"></i></a></td>""" in html)
        
            # badge present and displayed
            self.assertTrue("""title="no description available">testJenkinsKo2</a><span class="badge bg-primary" style="background-color: crimson !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&lt;&gt; &gt;getText on HtmlElement error message">getErrorMessage&lt;</span></td><td name="stepsTotal-1">4""" in html)
        
            # related error displayed and the canvas is accessible
            self.assertTrue("""<td name="relatedErrors-1"><a  href="#" data-bs-toggle="offcanvas" data-bs-target="#offcanvas-110" aria-controls="offcanvasRight">1</a><!-- canvas showing related errors -->""" in html)
            self.assertTrue("""<div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvas-110" aria-labelledby="offcanvasRightLabel"><div class="offcanvas-header"><h5 id="offcanvasRightLabel">Related errors</h5><button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button></div><div class="offcanvas-body"><table class="table">""" in html)
            self.assertTrue("""<div class="offcanvas-body"><table class="table"><th>Session</td><th>Test name</td><th>Test date</td><tr><td>May 5, 2023, 3:16 p.m.</td><td><a href='/snapshot/testResults/result/11/'>testJenkinsKo</a></td><td>May 5, 2023, 3:16 p.m.</td></tr></table></div></div></td><""" in html)
        
    def test_summary_report_result_ko_with_recorded_error_with_related_and_same_error(self):
        """
        Same as test_summary_report_result_ko but there are 2 tests with the same error
        This time, a related error has also been found
        Check
        - a badge is present for the failed test, badge is the same for the 2 tests
        - number of related error is displayed and canvas is accessible
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            # add an other result is Session 1
            tcis = TestCaseInSession.objects.get(pk=110)
            session = TestSession.objects.get(pk=11)
            tcis.session = session
            tcis.save()
            
            # record error for test_case_in_session=11
            error = Error(stepResult=StepResult.objects.get(id=13),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error.save()
            
            # record error for test_case_in_session=110
            error110 = Error(stepResult=StepResult.objects.get(id=130),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error110.save()
            error110.relatedErrors.set([error])
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 11}))
            self.assertEqual(2, len(response.context['object_list']))
            
            # check content of tests
            object_list_iterator = iter(response.context['object_list'].items())
            test_case_in_session, test_case_info = next(object_list_iterator)
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEquals([TestCaseInSession.objects.get(id=110)], test_case_info[4]) # the other test is returned
            self.assertEquals({'id': 0, 'error_short': 'getErrorMessage<', 'error': 'Error WebDriverException in search in getErrorMessage<> >getText on HtmlElement error message', 'color': 'crimson'}, test_case_info[5]) # badge information => information about the error
            
            test_case_in_session, test_case_info = next(object_list_iterator)
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEquals([TestCaseInSession.objects.get(id=11)], test_case_info[4]) # the other test is returned
            self.assertEquals({'id': 0, 'error_short': 'getErrorMessage<', 'error': 'Error WebDriverException in search in getErrorMessage<> >getText on HtmlElement error message', 'color': 'crimson'}, test_case_info[5]) # badge information => information about the error
    
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # related error displayed and the canvas is accessible
            self.assertTrue("""<td name="relatedErrors-1"><a  href="#" data-bs-toggle="offcanvas" data-bs-target="#offcanvas-11" aria-controls="offcanvasRight">1</a><!-- canvas showing related errors -->""" in html)
            self.assertTrue("""<div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvas-11" aria-labelledby="offcanvasRightLabel"><div class="offcanvas-header"><h5 id="offcanvasRightLabel">Related errors</h5><button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button></div><div class="offcanvas-body"><table class="table">""" in html)
            self.assertTrue("""<div class="offcanvas-body"><table class="table"><th>Session</td><th>Test name</td><th>Test date</td><tr><td>May 5, 2023, 3:16 p.m.</td><td><a href='/snapshot/testResults/result/110/'>testJenkinsKo2</a></td><td>May 5, 2023, 3:20 p.m.</td></tr></table></div></div></td><""" in html)
        
            self.assertTrue("""<td name="relatedErrors-2"><a  href="#" data-bs-toggle="offcanvas" data-bs-target="#offcanvas-110" aria-controls="offcanvasRight">1</a><!-- canvas showing related errors -->""" in html)
            self.assertTrue("""<div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvas-110" aria-labelledby="offcanvasRightLabel"><div class="offcanvas-header"><h5 id="offcanvasRightLabel">Related errors</h5><button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button></div><div class="offcanvas-body"><table class="table">""" in html)
            self.assertTrue("""<div class="offcanvas-body"><table class="table"><th>Session</td><th>Test name</td><th>Test date</td><tr><td>May 5, 2023, 3:16 p.m.</td><td><a href='/snapshot/testResults/result/11/'>testJenkinsKo</a></td><td>May 5, 2023, 3:16 p.m.</td></tr></table></div></div></td><""" in html)
        
            # both tests have the same badge as error is the same
            self.assertTrue("""title="no description available">testJenkinsKo2</a><span class="badge bg-primary" style="background-color: crimson !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&lt;&gt; &gt;getText on HtmlElement error message">getErrorMessage&lt;</span></td><td name="stepsTotal-2">4""" in html)
            self.assertTrue("""title="no description available">testJenkinsKo</a><span class="badge bg-primary" style="background-color: crimson !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&lt;&gt; &gt;getText on HtmlElement error message">getErrorMessage&lt;</span></td><td name="stepsTotal-1">5""" in html)
    
    def test_summary_report_result_ko_with_recorded_error_with_related_and_different_error(self):
        """
        Same as test_summary_report_result_ko but there are 2 tests with different error
        This time, a related error has also been found
        Check
        - a badge is present for the failed test, badge is different for each test
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            # add an other result is Session 1
            tcis = TestCaseInSession.objects.get(pk=110)
            session = TestSession.objects.get(pk=11)
            tcis.session = session
            tcis.save()
            
            # record error for test_case_in_session=11
            error = Error(stepResult=StepResult.objects.get(id=13),
                          action="getErrorMessage<> >getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error.save()
            
            # record error for test_case_in_session=110
            error110 = Error(stepResult=StepResult.objects.get(id=130),
                          action="getErrorMessage>getText on HtmlElement error message",
                          exception="WebDriverException",
                          errorMessage="WebDriverException in search")
            error110.save()
            
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 11}))
            self.assertEqual(2, len(response.context['object_list']))
            
            # check content of tests
            object_list_iterator = iter(response.context['object_list'].items())
            test_case_in_session, test_case_info = next(object_list_iterator)
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEquals([], test_case_info[4]) # the other test is returned
            self.assertEquals({'id': 0, 'error_short': 'getErrorMessage<', 'error': 'Error WebDriverException in search in getErrorMessage<> >getText on HtmlElement error message', 'color': 'crimson'}, test_case_info[5]) # badge information => information about the error
            
            test_case_in_session, test_case_info = next(object_list_iterator)
            self.assertEqual(11, response.context['testSession'].id)
            self.assertEquals([], test_case_info[4]) # the other test is returned
            self.assertEquals({'id': 1, 'error_short': 'getErrorMessage', 'error': 'Error WebDriverException in search in getErrorMessage>getText on HtmlElement error message', 'color': 'coral'}, test_case_info[5]) # badge information => information about the error
    
            # check content
            html = self.remove_spaces(response.rendered_content)
    
            # both tests have the same badge as error is the same
            self.assertTrue("""title="no description available">testJenkinsKo2</a><span class="badge bg-primary" style="background-color: coral !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&gt;getText on HtmlElement error message">getErrorMessage</span></td><td name="stepsTotal-2">4""" in html)
            self.assertTrue("""title="no description available">testJenkinsKo</a><span class="badge bg-primary" style="background-color: crimson !important" data-bs-toggle="tooltip" title="Error WebDriverException in search in getErrorMessage&lt;&gt; &gt;getText on HtmlElement error message">getErrorMessage&lt;</span></td><td name="stepsTotal-1">5""" in html)
        
    def test_summary_report_result_skipped(self):
        """
        Check that the test is displayed in summary
        - link to individual test is ok
        - number of failed steps is ok
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_results_application_myapp')))
        
            response = self.client.get(reverse('testSessionSummaryView', kwargs={'sessionId': 111}))
            self.assertEqual(1, len(response.context['object_list']))
            
            # check order of steps
            test_case_in_session, test_case_info = next(iter(response.context['object_list'].items()))
            
            self.assertEqual(111, response.context['testSession'].id)
            self.assertEqual([], response.context['testInfoList'])
            self.assertEquals(111, test_case_in_session.id)
            self.assertIsNone(test_case_info[0]) # no snapshot comparison done
            self.assertEquals(0, test_case_info[1]) # number of steps
            self.assertEquals(0, test_case_info[2]) # number of failed steps
            self.assertEquals(0, test_case_info[3]) # test duration
            self.assertEquals({}, test_case_info[6]) # test info
     
            # check content
            html = self.remove_spaces(response.rendered_content)
            
            # test is SKIPPED
            self.assertTrue("""<tr class="testSkipped"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/111/' info="skipped" data-bs-toggle="tooltip" title="no description available">testJenkins</a>""" in html)
         
