from datetime import timedelta

from django.utils import timezone

from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import StepResult, Error, TestCaseInSession, TestCase, TestSession
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetStepResult(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_stepresult = ContentType.objects.get_for_model(StepResult)

    def _create_stepresult(self, expected_status):
        response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': True, 'stacktrace': '{"foo": "bar"}'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(StepResult.objects.filter(stacktrace='{"foo": "bar"}')))

    def test_stepresult_create_with_model_permission(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_stepresult', content_type=self.content_type_stepresult)))
        self._create_stepresult(201)

    def test_stepresult_other_verbs_forbidden(self):
        """
        Check we cann only post sessions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_stepresult', content_type=self.content_type_stepresult)
                                                                                      | Q(codename='change_stepresult', content_type=self.content_type_stepresult)
                                                                                      | Q(codename='delete_stepresult', content_type=self.content_type_stepresult)))
        response = self.client.get('/snapshot/api/stepresult/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/stepresult/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/stepresult/1/')
        self.assertEqual(405, response.status_code)

    def test_stepresult_create_no_api_security(self):
        """
        Check it's possible to add a stepresult when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_stepresult(201)

    def test_stepresult_create_forbidden(self):
        """
        Check it's NOT possible to add a stepresult without 'add_stepresult' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_stepresult', content_type=self.content_type_stepresult)))
        self._create_stepresult(403)

    def test_stepresult_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_stepresult permission
        - has NOT app1 permission

        User can add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_stepresult', content_type=self.content_type_stepresult)))
            self._create_stepresult(201)

    def test_stepresult_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_stepresult permission
        - has app1 permission

        User can add test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_stepresult(201)

    def test_stepresult_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_stepresult permission
        - has app1 permission

        User can NOT add test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_stepresult(403)

    def test_stepresult_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_stepresult permission
        - has NOT app1 permission

        User can NOT add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_stepresult')))
            self._create_stepresult(403)

    def _update_stepresult(self, expected_status):
        response = self.client.patch(f'/snapshot/api/stepresult/1/', data={'stacktrace': '{"logs": "updated"}'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual('{"logs": "updated"}', StepResult.objects.get(pk=1).stacktrace)

    def test_stepresult_update_with_model_permission(self):
        """
        Test it's possible to update session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_stepresult', content_type=self.content_type_stepresult)))
        self._update_stepresult(200)

    def test_stepresult_update_non_existent_object(self):
        """
        Test it's possible to update session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_stepresult', content_type=self.content_type_stepresult)))
        response = self.client.patch(f'/snapshot/api/stepresult/12345/', data={'name': 'bla2'})
        self.assertEqual(404, response.status_code)

    def test_stepresult_update_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_stepresult permission
        - has app1 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._update_stepresult(200)

    def test_stepresult_update_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT change_stepresult permission
        - has app1 permission

        User can NOT update test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._update_stepresult(403)

    def test_stepresult_parse_stacktrace_result_ok(self):
        """
        When no error in step, stacktrace is not parsed
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": false,
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "SUCCESS",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': True, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            self.assertEqual(0, len(Error.objects.all()))

    def test_stepresult_parse_stacktrace_not_present(self):
        """
        Check no error is raised when stacktrace is empty
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': ''})
            self.assertEqual(201, response.status_code)
            self.assertEqual(0, len(Error.objects.all()))

    def test_stepresult_parse_stacktrace_result_ko(self):
        """
        When error in step, stacktrace is parsed but missing field prevent creating error
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            self.assertEqual(0, len(Error.objects.all()))

    def test_stepresult_parse_stacktrace_result_ko_step_failed(self):
        """
        When error in step, stacktrace is parsed and a new error is created
        Error action is the name of the step because no sub-step has failed
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error = Error.objects.all()[0]

            self.assertEqual('openPage with args: (https://jenkins/jenkins/, )', error.action)
            self.assertIsNone(error.cause)
            self.assertEqual('class java.lang.AssertionError: expected [false] but <_> found [true]', error.errorMessage)
            self.assertEqual('class java.lang.AssertionError', error.exception)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_parsed_2_times(self):
        """
        If error is created on a first parse, updating stacktrace sould delete the previous errors as stacktrace has evolved
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error1 = Error.objects.get(stepResult=step_result_id)

            response = self.client.patch(f'/snapshot/api/stepresult/{step_result_id}/', data={'stacktrace': stacktrace.replace("AssertionError", "AssertionError2")})
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, len(Error.objects.filter(stepResult=step_result_id)))
            self.assertNotEqual(error1.id, Error.objects.get(stepResult=step_result_id).id)


    def test_stepresult_parse_stacktrace_result_ko_related_error(self):
        """
        Check that if the same error happened in the last hour, it's linked to this error
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        tcis1 = TestCaseInSession(testCase=TestCase.objects.get(pk=1), session=TestSession.objects.get(pk=1), date=timezone.now())
        tcis1.save()
        tcis2 = TestCaseInSession(testCase=TestCase.objects.get(pk=2), session=TestSession.objects.get(pk=1), date=timezone.now())
        tcis2.save()

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))

            # create a first stepResult which will generate an error
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis1.id, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id1 = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error1 = Error.objects.get(stepResult=step_result_id1)

            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis2.id, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id2 = response.data['id']
            self.assertEqual(2, len(Error.objects.all()))
            error2 = Error.objects.get(stepResult=step_result_id2)

            self.assertEqual(1, len(error1.relatedErrors.all()))
            self.assertEqual(1, len(error2.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_related_error_too_old(self):
        """
        Check that if the same error happened previous to the last hour, it's NOT linked to this error
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        tcis1 = TestCaseInSession(testCase=TestCase.objects.get(pk=1), session=TestSession.objects.get(pk=1), date=timezone.now() - timedelta(seconds=3601))
        tcis1.save()
        tcis2 = TestCaseInSession(testCase=TestCase.objects.get(pk=2), session=TestSession.objects.get(pk=1), date=timezone.now())
        tcis2.save()

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))

            # create a first stepResult which will generate an error
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis1.id, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id1 = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error1 = Error.objects.get(stepResult=step_result_id1)

            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis2.id, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id2 = response.data['id']
            self.assertEqual(2, len(Error.objects.all()))
            error2 = Error.objects.get(stepResult=step_result_id2)

            self.assertEqual(0, len(error1.relatedErrors.all()))
            self.assertEqual(0, len(error2.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_related_error_different(self):
        """
        Check that if an other error happened in the last hour, it's NOT linked to this error
        this test checks difference on
        - action
        - exception
        - exception message
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        tcis1 = TestCaseInSession(testCase=TestCase.objects.get(pk=1), session=TestSession.objects.get(pk=1), date=timezone.now())
        tcis1.save()
        tcis2 = TestCaseInSession(testCase=TestCase.objects.get(pk=2), session=TestSession.objects.get(pk=1), date=timezone.now())
        tcis2.save()

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))

            # create a first stepResult which will generate an error
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis1.id, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id1 = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error1 = Error.objects.get(stepResult=step_result_id1)

            # difference on message
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis2.id, 'result': False, 'stacktrace': stacktrace.replace("class java.lang.AssertionError: expected", "class java.lang.AssertionError2: expected")})
            self.assertEqual(201, response.status_code)
            step_result_id2 = response.data['id']
            error2 = Error.objects.get(stepResult=step_result_id2)

            # difference on exception
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis2.id, 'result': False, 'stacktrace': stacktrace.replace("class java.lang.AssertionError", "class java.lang.AssertionError2")})
            self.assertEqual(201, response.status_code)
            step_result_id3 = response.data['id']
            error3 = Error.objects.get(stepResult=step_result_id3)

            # difference on action
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': tcis2.id, 'result': False, 'stacktrace': stacktrace.replace('"action": "openPage"', '"action": "openPage2"').replace('"name": "openPage', '"name": "openPage2')})
            self.assertEqual(201, response.status_code)
            step_result_id4 = response.data['id']
            error4 = Error.objects.get(stepResult=step_result_id4)

            self.assertEqual(0, len(error1.relatedErrors.all()))
            self.assertEqual(0, len(error2.relatedErrors.all()))
            self.assertEqual(0, len(error3.relatedErrors.all()))
            self.assertEqual(0, len(error4.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_action_failed(self):
        """
        When error in step, stacktrace is parsed and a new error is created
        Error action is the path to the sub-step because one has failed
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "action": "openPage",
                    "origin": "LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "action": "setWindowToRequestedSize",
                    "origin": "LoginPage",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error = Error.objects.all()[0]

            self.assertEqual('openPage>setWindowToRequestedSize in LoginPage', error.action)
            self.assertIsNone(error.cause)
            self.assertEqual('class java.lang.AssertionError: expected [false] but <_> found [true]', error.errorMessage)
            self.assertEqual('class java.lang.AssertionError', error.exception)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_action_failed_on_element(self):
        """
        When error in step, stacktrace is parsed and a new error is created
        The action that failed is a click on element, so reported action mentions element
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "action": "openPage",
                    "origin": "LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "click on ButtonElement connect, by={By.name: Submit} ",
                    "action": "click",
                    "origin": "LoginPage",
                    "element": "connect",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error = Error.objects.all()[0]

            self.assertEqual('openPage>click on LoginPage.connect', error.action)
            self.assertIsNone(error.cause)
            self.assertEqual('class java.lang.AssertionError: expected [false] but <_> found [true]', error.errorMessage)
            self.assertEqual('class java.lang.AssertionError', error.exception)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_action_failed_on_element_with_exception(self):
        """
        When error in step, stacktrace is parsed and a new error is created
        The action that failed is a click on element, and an exception is also present in the action.
        So this is the action exception that is used
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "action": "openPage",
                    "origin": "LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "click on ButtonElement connect, by={By.name: Submit} ",
                    "action": "click",
                    "origin": "LoginPage",
                    "element": "connect",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "exception": "class org.openqa.selenium.WebDriverException",
                    "exceptionMessage": "class org.openqa.selenium.WebDriverException: element not found",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']
            self.assertEqual(1, len(Error.objects.all()))
            error = Error.objects.all()[0]

            self.assertEqual('openPage>click on LoginPage.connect', error.action)
            self.assertIsNone(error.cause)
            self.assertEqual('class org.openqa.selenium.WebDriverException: element not found', error.errorMessage)
            self.assertEqual('class org.openqa.selenium.WebDriverException', error.exception)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_on_update(self):
        """
        Check that stacktrace is also parsed on update
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "openPage with args: (https://jenkins/jenkins/, )",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "action": "openPage",
                    "origin": "LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "click on ButtonElement connect, by={By.name: Submit} ",
                    "action": "click",
                    "origin": "LoginPage",
                    "element": "connect",
                    "failed": true,
                    "position": 1,
                    "type": "action",
                    "exception": "class org.openqa.selenium.WebDriverException",
                    "exceptionMessage": "class org.openqa.selenium.WebDriverException: element not found",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': '{}'})
            self.assertEqual(0, len(Error.objects.all()))
            self.assertEqual(201, response.status_code)
            step_result_id = response.data['id']

            response = self.client.patch(f'/snapshot/api/stepresult/{step_result_id}/', data={'stacktrace': stacktrace})
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, len(Error.objects.all()))
            error = Error.objects.all()[0]

            self.assertEqual('openPage>click on LoginPage.connect', error.action)
            self.assertIsNone(error.cause)
            self.assertEqual('class org.openqa.selenium.WebDriverException: element not found', error.errorMessage)
            self.assertEqual('class org.openqa.selenium.WebDriverException', error.exception)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_test_end(self):
        """
        Test end error should not be parsed even if it's KO
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "exception": "class java.lang.AssertionError",
            "exceptionMessage": "class java.lang.AssertionError: expected [false] but <_> found [true]",
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "Test end",
            "action": "Test end",
            "files": [],
            "position": 0,
            "actions": [
                {
                    "name": "Opening page LoginPage",
                    "failed": false,
                    "position": 0,
                    "type": "action",
                    "timestamp": 1698245638815
                },
                {
                    "name": "setWindowToRequestedSize on on page LoginPage ",
                    "failed": false,
                    "position": 1,
                    "type": "action",
                    "timestamp": 1698245638816
                }
            ],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
            self.assertEqual(201, response.status_code)
            self.assertEqual(0, len(Error.objects.all()))


