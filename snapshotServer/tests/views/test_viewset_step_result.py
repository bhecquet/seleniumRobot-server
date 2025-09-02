'''
Created on 16 mai 2017

@author: bhecquet
'''

from rest_framework.test import APITestCase
from snapshotServer.tests import authenticate_test_client_for_api
from snapshotServer.models import Error, StepResult, TestCase, TestStep, TestSession, TestCaseInSession, TestEnvironment
import datetime
import pytz
from variableServer.models import Version
from django.utils import timezone

class TestViewsetStepResult(APITestCase):
    fixtures = ['testresult_commons.yaml', 'testresult_ok.yaml', 'testresult_ko.yaml']
    
    step_ko_details = """
        {
    "exception": "org.openqa.selenium.NoSuchElementException",
    "date": "Fri May 02 17:44:55 CEST 2025",
    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
    "failed": true,
    "type": "step",
    "duration": 32298,
    "snapshots": [
        {
            "exception": "org.openqa.selenium.NoSuchElementException",
            "idHtml": null,
            "displayInReport": false,
            "name": "Step beginning state",
            "idImage": 67,
            "failed": false,
            "position": 0,
            "type": "snapshot",
            "snapshotCheckType": "NONE_REFERENCE",
            "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\n",
            "timestamp": 1746207928066
        }
    ],
    "videoTimeStamp": 1256,
    "name": "_loginInvalid with args: (foo, bar, )",
    "action": "_loginInvalid",
    "files": [],
    "position": 2,
    "actions": [
        {
            "exception": "org.openqa.selenium.NoSuchElementException",
            "date": "Fri May 02 17:44:55 CEST 2025",
            "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
            "failed": true,
            "type": "step",
            "duration": 0,
            "snapshots": [],
            "videoTimeStamp": 0,
            "name": "connect with args: (foo, bar, )",
            "action": "connect",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "exception": "org.openqa.selenium.NoSuchElementException",
                    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
                    "name": "sendKeys on TextFieldElement user, by={By.id: j_username} with args: (true, true, [foo,], )",
                    "action": "sendKeys",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                    "timestamp": 1746207895053,
                    "element": "user"
                },
                {
                    "exception": "org.openqa.selenium.NoSuchElementException",
                    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
                    "name": "sendKeys on TextFieldElement password, by={By.name: j_passwor} with args: (true, true, [bar,], )",
                    "action": "sendKeys",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                    "timestamp": 1746207895478,
                    "element": "password"
                },
                {
                    "messageType": "WARNING",
                    "name": "Warning: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\nFor documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#no-such-element-exception\\nBuild info: version: '4.28.1', revision: '73f5ad48a2'\\nSystem info: os.name: 'Windows 11', os.arch: 'amd64', os.version: '10.0', java.version: '21.0.1'\\nDriver info: driver.version: unknown\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect_aroundBody12(LoginPage.java:55)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect(LoginPage.java:53)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect_aroundBody6(LoginPage.java:43)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody8(LoginPage.java:43)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody10(LoginPage.java:42)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid(LoginPage.java:42)",
                    "type": "message"
                }
            ],
            "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
            "timestamp": 1746207895052,
            "status": "FAILED",
            "harCaptures": []
        }
    ],
    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
    "timestamp": 1746207895052,
    "status": "FAILED",
    "harCaptures": []
}"""

    step_multiple_actions_ko_details = """
        {
    "exception": "org.openqa.selenium.NoSuchElementException",
    "date": "Fri May 02 17:44:55 CEST 2025",
    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
    "failed": true,
    "type": "step",
    "duration": 32298,
    "snapshots": [
        {
            "exception": "org.openqa.selenium.NoSuchElementException",
            "idHtml": null,
            "displayInReport": false,
            "name": "Step beginning state",
            "idImage": 67,
            "failed": false,
            "position": 0,
            "type": "snapshot",
            "snapshotCheckType": "NONE_REFERENCE",
            "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\n",
            "timestamp": 1746207928066
        }
    ],
    "videoTimeStamp": 1256,
    "name": "_loginInvalid with args: (foo, bar, )",
    "action": "_loginInvalid",
    "files": [],
    "position": 2,
    "actions": [
        {
            "exception": "org.openqa.selenium.NoSuchElementException",
            "date": "Fri May 02 17:44:55 CEST 2025",
            "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
            "failed": true,
            "type": "step",
            "duration": 0,
            "snapshots": [],
            "videoTimeStamp": 0,
            "name": "connect with args: (foo, bar, )",
            "action": "connect",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "exception": "org.openqa.selenium.NoSuchElementException",
                    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
                    "name": "sendKeys on TextFieldElement user, by={By.id: j_username} with args: (true, true, [foo,], )",
                    "action": "sendKeys",
                    "failed": true,
                    "position": 0,
                    "type": "action",
                    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                    "timestamp": 1746207895053,
                    "element": "user"
                },
                {
                    "exception": "org.openqa.selenium.NoSuchElementException",
                    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
                    "name": "sendKeys on TextFieldElement password, by={By.name: j_passwor} with args: (true, true, [bar,], )",
                    "action": "sendKeys",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                    "timestamp": 1746207895478,
                    "element": "password"
                },
                {
                    "messageType": "WARNING",
                    "name": "Warning: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\nFor documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#no-such-element-exception\\nBuild info: version: '4.28.1', revision: '73f5ad48a2'\\nSystem info: os.name: 'Windows 11', os.arch: 'amd64', os.version: '10.0', java.version: '21.0.1'\\nDriver info: driver.version: unknown\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect_aroundBody12(LoginPage.java:55)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect(LoginPage.java:53)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage.connect_aroundBody6(LoginPage.java:43)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody8(LoginPage.java:43)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid_aroundBody10(LoginPage.java:42)\\nat company.pic.jenkins.tests.selenium.webpage.LoginPage._loginInvalid(LoginPage.java:42)",
                    "type": "message"
                }
            ],
            "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
            "timestamp": 1746207895052,
            "status": "FAILED",
            "harCaptures": []
        }
    ],
    "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
    "timestamp": 1746207895052,
    "status": "FAILED",
    "harCaptures": []
}"""

    step_ok_details = """
        {
    "exception": "",
    "date": "Fri May 02 17:44:55 CEST 2025",
    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
    "failed": false,
    "type": "step",
    "duration": 32298,
    "snapshots": [
    ],
    "videoTimeStamp": 1256,
    "name": "_loginInvalid with args: (foo, bar, )",
    "action": "_loginInvalid",
    "files": [],
    "position": 2,
    "actions": [
        {
            "exception": "",
            "date": "Fri May 02 17:44:55 CEST 2025",
            "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
            "failed": false,
            "type": "step",
            "duration": 0,
            "snapshots": [],
            "videoTimeStamp": 0,
            "name": "connect with args: (foo, bar, )",
            "action": "connect",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "exception": "",
                    "origin": "company.pic.jenkins.tests.selenium.webpage.LoginPage",
                    "name": "sendKeys on TextFieldElement user, by={By.id: j_username} with args: (true, true, [foo,], )",
                    "action": "sendKeys",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "exceptionMessage": "",
                    "timestamp": 1746207895053,
                    "element": "user"
                }
            ],
            "exceptionMessage": "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found\\n",
            "timestamp": 1746207895052,
            "status": "FAILED",
            "harCaptures": []
        }
    ],
    "exceptionMessage": "",
    "timestamp": 1746207895052,
    "status": "SUCCESS",
    "harCaptures": []
}"""
    
    def setUp(self):
        authenticate_test_client_for_api(self.client)
        
        testCase = TestCase.objects.get(id=1)
        step1 = TestStep.objects.get(id=1)
        
        session1 = TestSession(sessionId="1237", date=datetime.datetime.now(tz=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        session1.save()
        self.tcs1 = TestCaseInSession(testCase=testCase, session=session1, date=timezone.now() - datetime.timedelta(seconds=3590))
        self.tcs1.save()
        self.sr1 = StepResult(step=step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        
    def test_parse_step_result_ko(self):
        """
        Check an error is created when a step action failed
        """
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 1)
        
    def test_parse_step_result_ko2(self):
        """
        Check only one error is created when multiple step action fail
        """
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_multiple_actions_ko_details})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 1)
        
    def test_parse_step_result_ko_test_end_step(self):
        """
        Check "Test end" step won't be analyzed
        """
        
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details.replace("_loginInvalid with args: (foo, bar, )", "Test end")})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 0)
        
    def test_parse_step_result_ko_with_similar_errors(self):
        """
        Check we find similar errors in the last hour
        """
       
        error1 = Error(stepResult = self.sr1,
                              action = "getErrorMessage<> >getText on errorMessage",
                              exception = "Assertion",
                              errorMessage = "Assertion Failure: expected [false] but found [true]",
                              )
        error1.save()
        error2 = Error(stepResult = self.sr1,
                              action = "_loginInvalid>connect>sendKeys on company.pic.jenkins.tests.selenium.webpage.LoginPage.password",
                              exception = "org.openqa.selenium.NoSuchElementException",
                              errorMessage = "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                              )
        error2.save()
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 2) # 2 errors, the existing one, and the newly recorded
        self.assertEqual(len(Error.objects.latest('id').relatedErrors.all()), 1)
        self.assertEqual(Error.objects.latest('id').relatedErrors.all()[0].id, error2.id)
    
        
    def test_parse_step_result_ko_with_almost_matching_errors(self):
        """
        Check we do not attach other errors when action differs
        """
       
        error1 = Error(stepResult = self.sr1,
                              action = "_loginValid>connect>sendKeys on company.pic.jenkins.tests.selenium.webpage.LoginPage.password",
                              exception = "org.openqa.selenium.NoSuchElementException",
                              errorMessage = "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                              )
        error1.save()
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.latest('id').relatedErrors.all()), 0)
        
    def test_parse_step_result_ko_with_almost_matching_errors2(self):
        """
        Check we do not attach other errors when exception differs
        """
       
        error1 = Error(stepResult = self.sr1,
                              action = "_loginInvalid>connect>sendKeys on company.pic.jenkins.tests.selenium.webpage.LoginPage.password",
                              exception = "org.openqa.selenium.NoElementException",
                              errorMessage = "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                              )
        error1.save()
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.latest('id').relatedErrors.all()), 0)
    
        
    def test_parse_step_result_ko_with_almost_matching_errors3(self):
        """
        Check we do not attach other errors when error message differs
        """
       
        error1 = Error(stepResult = self.sr1,
                              action = "_loginInvalid>connect>sendKeys on company.pic.jenkins.tests.selenium.webpage.LoginPage.password",
                              exception = "org.openqa.selenium.NoSuchElementException",
                              errorMessage = "class org.openqa.selenium.NoElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                              )
        error1.save()
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.latest('id').relatedErrors.all()), 0)
    
    def test_parse_step_result_ko_with_similar_errors_earlier(self):
        """
        Check we cannot find similar errors in the last hour
        """
        self.tcs1.date = timezone.now() - datetime.timedelta(seconds=3601)
        self.tcs1.save()

        error1 = Error(stepResult = self.sr1,
                              action = "getErrorMessage<> >getText on errorMessage",
                              exception = "Assertion",
                              errorMessage = "Assertion Failure: expected [false] but found [true]",
                              )
        error1.save()
        error2 = Error(stepResult = self.sr1,
                              action = "_loginInvalid>connect>sendKeys on company.pic.jenkins.tests.selenium.webpage.LoginPage.password",
                              exception = "org.openqa.selenium.NoSuchElementException",
                              errorMessage = "class org.openqa.selenium.NoSuchElementException: Searched element [TextFieldElement password, by={By.name: j_passwor}] from page 'company.pic.jenkins.tests.selenium.webpage.LoginPage' could not be found",
                              )
        error2.save()
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 2) # 2 errors, the existing one, and the newly recorded
        self.assertEqual(len(Error.objects.latest('id').relatedErrors.all()), 0)
    
        
    def test_parse_step_result_ok(self):
        """
        Check an error is created when a step action failed
        """
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ok_details})
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 0)
    
        
    def test_parse_step_result_invalid_json(self):
        """
        If error occurs while parsing, do not preven
        """
        response = self.client.patch('/snapshot/api/stepresult/13/', data={'stacktrace':  self.step_ko_details[:-1]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")), 0)
    