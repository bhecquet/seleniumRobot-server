from snapshotServer.tests import SnapshotTestCase,\
    authenticate_test_client_for_web_view
from django.conf import settings
import os
from django.test.client import Client
from django.urls.base import reverse
from snapshotServer.models import StepResult, Snapshot, TestSession,\
    TestCaseInSession


class TestTestsSummaryView(SnapshotTestCase):

    fixtures = ['tests_summary_commons.yaml', 'tests_summary_ok.yaml', 'tests_summary_ko.yaml', 'tests_summary_skipped.yaml', 'tests_summary_snapshot_comparison.yaml']
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    # summary 2 tests 
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        authenticate_test_client_for_web_view(self.client)
        
           
    def test_summary_report_result_ok(self):
        """
        Check that the test is displayed in summary
        - last state image is available
        - link to individual test is ok
        """
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
        self.assertEquals({'Issue': {'type': 'hyperlink', 'link': 'https://jiraserver/PROJECT/PRO-1', 'info': 'Issue'}, 'Some information': {'type': 'string', 'info': 'some text'}, 'Last State': {'type': 'multipleinfo', 'infos': [{'link': 'loginInvalid_3-1_Test_end--9a514b.png', 'id': 90, 'type': 'imagelink', 'info': 'Image'}, {'link': 'videoCapture.avi', 'id': 91, 'type': 'videolink', 'info': 'Video'}]}}, test_case_info[4]) # test duration
        
        # check content
        html = self.remove_spaces(response.rendered_content)
        
        # shortcut to image / video present
        self.assertTrue("""<td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
        # link to detailed result
        self.assertTrue("""<tr class="testSuccess"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/1/' info="ok" data-toggle="tooltip" title="no description available">testJenkins</a></td>""" in html)
        # step count +  duration
        self.assertTrue("""<td name="stepsTotal-1">4</td><td>7 sec.</td>""" in html)
        # additional test information
        self.assertTrue("""<td><a href="https://jiraserver/PROJECT/PRO-1">Issue</a></td><td>some text</td>""" in html)
        
           
    def test_summary_report_contains_multiple_tests(self):
        """
        Check that multiple tests can be displayed in the report
        """
        
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
        print(html)
        
        # shortcut to image / video present
        self.assertTrue("""<td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
        # link to detailed result
        self.assertTrue("""<tr class="testSuccess"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/1/' info="ok" data-toggle="tooltip" title="no description available">testJenkins</a></td>""" in html)
        # step count +  duration
        self.assertTrue("""<td name="stepsTotal-2">4</td><td>7 sec.</td>""" in html)
        # additional test information
        self.assertTrue("""<td>7 sec.</td><td><a href="https://jiraserver/PROJECT/PRO-1">Issue</a></td><td>some text</td><td><a href="/snapshot/api/file/90/download/"><i class="fas fa-file-image" aria-hidden="true"></i></a><a href="/snapshot/api/file/91/download/"><i class="fas fa-video" aria-hidden="true"></i></a></td>""" in html)
        
        # test KO is also present
        self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/11/' info="ko" data-toggle="tooltip" title="no description available">testJenkinsKo</a></td>""" in html)
        # information are in the right cell
        self.assertTrue("""<td>12 sec.</td><td></td><td></td><td><a class="errorTooltip"><i class="fas fa-file-alt" aria-hidden="true" data-toggle="popover" title="Exception" data-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"></i></a></td></tr>""" in html)
          
        # chek test order depends on date
        self.assertTrue(html.find(">testJenkinsKo<") < html.find(">testJenkins<"))
               
    def test_summary_report_result_ok_with_snapshot_comparison_ok(self):
        """
        Check that the icon for snapshot comparison is present
        """
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
        self.assertTrue("""<i class="fa-solid fa-code-compare font-success" data-toggle="tooltip" title="snapshot comparison successful"></i><a href='/snapshot/testResults/result/1/' info="ok" data-toggle="tooltip" title="no description available">testJenkins</a>""" in html)

        
    def test_summary_report_result_ok_with_snapshot_comparison_ko(self):
        """
        Check that the icon for snapshot comparison is present and red
        """
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
        self.assertTrue("""<i class="fa-solid fa-code-compare font-failed" data-toggle="tooltip" title="snapshot comparison failed"></i><a href='/snapshot/testResults/result/1/' info="ok" data-toggle="tooltip" title="no description available">testJenkins</a>""" in html)

    def test_summary_report_result_ko(self):
        """
        Check that the test is displayed in summary
        - link to individual test is ok
        - number of failed steps is ok
        """
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
        self.assertEquals({'Last State': {'type': 'multipleinfo', 'infos': [{'type': 'log', 'info': 'Browsermob proxy (captureNetwork option) is only compatible with DIRECT and <MANUAL>'}]}}, test_case_info[4]) # test info
 
        # check content
        html = self.remove_spaces(response.rendered_content)
        
        # test is KO
        self.assertTrue("""<tr class="testFailed"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/11/' info="ko" data-toggle="tooltip" title="no description available">testJenkinsKo</a></td>""" in html)
         
        # error message displayed
        self.assertTrue("""<a class="errorTooltip"><i class="fas fa-file-alt" aria-hidden="true" data-toggle="popover" title="Exception" data-content="Browsermob proxy (captureNetwork option) is only compatible with DIRECT and &lt;MANUAL&gt;"></i></a></td>""" in html)
    
    def test_summary_report_result_skipped(self):
        """
        Check that the test is displayed in summary
        - link to individual test is ok
        - number of failed steps is ok
        """
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
        self.assertEquals({}, test_case_info[4]) # test info
 
        # check content
        html = self.remove_spaces(response.rendered_content)
        
        # test is SKIPPED
        self.assertTrue("""<tr class="testSkipped"><td>jenkins</td><td class="alignleft"><a href='/snapshot/testResults/result/111/' info="skipped" data-toggle="tooltip" title="no description available">testJenkins</a></td>""" in html)
         
