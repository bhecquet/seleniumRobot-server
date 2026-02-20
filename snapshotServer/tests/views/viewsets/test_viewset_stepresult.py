import time
from datetime import timedelta
from unittest import mock
from unittest.mock import patch

from django.utils import timezone

from snapshotServer.controllers.error_cause.error_cause_finder import ErrorCause, ErrorCauseFinder
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import StepResult, Error, TestCaseInSession, TestCase, TestSession, TestStep
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
        response = self.client.patch('/snapshot/api/stepresult/1/', data={'stacktrace': '{"logs": "updated"}'})
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
            self.assertEqual('', error.element)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_parsed_2_times(self):
        """
        If error is created on a first parse, updating stacktrace should delete the previous errors as stacktrace has evolved
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
            self.assertEqual('', error.element)
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
                    "elementDescription": "button described by 'submit'",
                    "elementType": "button",
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
            self.assertEqual("button described by 'submit'", error.element)
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
                    "elementDescription": "button described by 'submit'",
                    "elementType": "button",
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
            self.assertEqual("button described by 'submit'", error.element)
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
                    "elementDescription": "button described by 'submit'",
                    "elementType": "button",
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
            self.assertEqual("button described by 'submit'", error.element)
            self.assertEqual(step_result_id, error.stepResult.id)
            self.assertEqual(0, len(error.relatedErrors.all()))

    def test_stepresult_parse_stacktrace_result_ko_test_end(self):
        """
        Test end error should not be parsed if an other step is already KO
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

        failed_step_result = StepResult.objects.get(pk=1)
        failed_step_result.result = False
        failed_step_result.save()

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                response = self.client.post('/snapshot/api/stepresult/', data={'step': 5, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
                self.assertEqual(201, response.status_code)
                self.assertEqual(0, len(Error.objects.all()))


    def test_stepresult_parse_stacktrace_result_ko_test_end_without_other_failed_step(self):
        """
        Test end error should be parsed if no other step is already KO
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

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                response = self.client.post('/snapshot/api/stepresult/', data={'step': 5, 'testCase': 1, 'result': False, 'stacktrace': stacktrace})
                self.assertEqual(201, response.status_code)
                time.sleep(1)
                errors = Error.objects.all()
                self.assertEqual(1, len(errors))
                self.assertEqual('class java.lang.AssertionError: expected [false] but <_> found [true]', errors[0].errorMessage)
                self.assertEqual("script", errors[0].cause) # check error cause is linked to "Test end" step error

    def test_step_result_parse_stacktrace_multiple_actions_in_error(self):
        """
        Check only one error is created when multiple step action fail
        """
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
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.post('/snapshot/api/stepresult/', data={'step': 1, 'testCase': 1, 'result': False, 'stacktrace': step_multiple_actions_ko_details})
            self.assertEqual(1, len(Error.objects.filter(exception="org.openqa.selenium.NoSuchElementException")))

    failed_test_end_stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": true,
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "Test end",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [],
            "timestamp": 1698245638814,
            "status": "FAILED",
            "harCaptures": []
        }"""

    def test_stepresult_analyze_test_run_result_ko(self):
        """
        When error in step, error cause detection is performed
        """


        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()
                response = self.client.post('/snapshot/api/stepresult/', data={'step': 5, 'testCase': 5, 'result': False, 'stacktrace': self.failed_test_end_stacktrace})
                self.assertEqual(201, response.status_code)
                self.assertEqual(0, len(Error.objects.all()))
                time.sleep(1)
                error_cause_finder_instance.detect_cause.assert_called()

    def test_stepresult_analyze_test_run_result_ko_on_update(self):
        """
        When error in step, error cause detection is performed
        Do it on stepresult update
        """


        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()

                test_end_step_result = StepResult(step=TestStep.objects.get(pk=5), testCase=TestCaseInSession.objects.get(pk=5), result=False, stacktrace="")
                test_end_step_result.save()
                response = self.client.patch(f'/snapshot/api/stepresult/{test_end_step_result.id}/' , data={'stacktrace': self.failed_test_end_stacktrace})
                self.assertEqual(200, response.status_code)
                self.assertEqual(0, len(Error.objects.all()))
                time.sleep(1)
                error_cause_finder_instance.detect_cause.assert_called()

    def test_stepresult_analyze_test_run_result_ko_on_update_with_error(self):
        """
        If error occurs during detection, this has no impact on server reply
        """

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [Exception("some detection error")]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()

                error = Error(stepResult=failed_step_result, action="step1>action1", exception="WebDriverException", errorMessage="Error searching element")
                error.save()

                test_end_step_result = StepResult(step=TestStep.objects.get(pk=5), testCase=TestCaseInSession.objects.get(pk=5), result=False, stacktrace="")
                test_end_step_result.save()
                response = self.client.patch(f'/snapshot/api/stepresult/{test_end_step_result.id}/' , data={'stacktrace': self.failed_test_end_stacktrace})
                self.assertEqual(200, response.status_code)
                time.sleep(1)
                updated_error = Error.objects.get(pk=error.id)
                self.assertEqual("unknown", updated_error.cause)
                self.assertEqual("Error detecting cause: some detection error", updated_error.causeAnalysisErrors)

    def test_stepresult_analyze_test_run_result_ko_on_update_with_multiple_errors(self):
        """
        If scenario has multiple steps in error (mostly when assertions fail), then all errors will get the same cause
        """

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()
                failed_step_result2 = StepResult.objects.get(pk=6)
                failed_step_result2.result = False
                failed_step_result2.save()

                error = Error(stepResult=failed_step_result, action="step1>action1", exception="WebDriverException", errorMessage="Error searching element")
                error.save()
                error2 = Error(stepResult=failed_step_result2, action="step2>action1", exception="AssertionError", errorMessage="Assertion failed")
                error2.save()

                test_end_step_result = StepResult(step=TestStep.objects.get(pk=5), testCase=TestCaseInSession.objects.get(pk=5), result=False, stacktrace="")
                test_end_step_result.save()
                response = self.client.patch(f'/snapshot/api/stepresult/{test_end_step_result.id}/' , data={'stacktrace': self.failed_test_end_stacktrace})
                self.assertEqual(200, response.status_code)
                time.sleep(1)
                updated_error = Error.objects.get(pk=error.id)
                self.assertEqual("script", updated_error.cause)
                self.assertEqual("unknown", updated_error.causedBy)
                updated_error2 = Error.objects.get(pk=error2.id)
                self.assertEqual("script", updated_error2.cause)
                self.assertEqual("unknown", updated_error2.causedBy)
                error_cause_finder_instance.detect_cause.assert_called_once()

    def test_stepresult_analyze_test_run_result_ko_on_update_with_existing_error(self):
        """
        When error in step, error cause detection is performed
        Do it on stepresult update
        Check that detected cause is added to existing error of the failed step
        """

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, ["info1", "info2"])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()

                error = Error(stepResult=failed_step_result, action="step1>action1", exception="WebDriverException", errorMessage="Error searching element")
                error.save()

                test_end_step_result = StepResult(step=TestStep.objects.get(pk=5), testCase=TestCaseInSession.objects.get(pk=5), result=False, stacktrace="")
                test_end_step_result.save()
                response = self.client.patch(f'/snapshot/api/stepresult/{test_end_step_result.id}/' , data={'stacktrace': self.failed_test_end_stacktrace})
                self.assertEqual(200, response.status_code)
                time.sleep(1)
                error_cause_finder_instance.detect_cause.assert_called()

                # check error has been updated
                updated_error = Error.objects.get(pk=error.id)
                self.assertEqual("script", updated_error.cause)
                self.assertEqual("unknown", updated_error.causedBy)
                self.assertEqual("", updated_error.causeDetails)
                self.assertEqual("info1\ninfo2", updated_error.causeAnalysisErrors)

    def test_stepresult_analyze_test_run_result_ko_no_stacktrace(self):
        """
        If no stacktrace is given, it means we did not receive the step details, and then, analysis should not be performed
        """
        stacktrace = """
        {
        }"""

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                failed_step_result = StepResult.objects.get(pk=5)
                failed_step_result.result = False
                failed_step_result.save()
                response = self.client.post('/snapshot/api/stepresult/', data={'step': 5, 'testCase': 5, 'result': False, 'stacktrace': stacktrace})
                self.assertEqual(201, response.status_code)
                self.assertEqual(0, len(Error.objects.all()))
                time.sleep(1)
                error_cause_finder_instance.detect_cause.assert_not_called()

    def test_stepresult_analyze_test_run_result_ok(self):
        """
        When test is OK, error cause detection is not called
        """
        stacktrace = """
        {
            "date": "Wed Oct 25 14:53:58 CEST 2023",
            "failed": false,
            "type": "step",
            "duration": 713,
            "snapshots": [],
            "videoTimeStamp": 5,
            "name": "Test end",
            "action": "openPage",
            "files": [],
            "position": 0,
            "actions": [],
            "timestamp": 1698245638814,
            "status": "SUCCESS",
            "harCaptures": []
        }"""

        with patch('snapshotServer.controllers.error_cause.error_cause_finder.ErrorCauseFinder.__new__', autospec=True) as mock_error_cause_finder:
            error_cause_finder_instance = mock.MagicMock()
            mock_error_cause_finder.return_value = error_cause_finder_instance
            error_cause_finder_instance.detect_cause.side_effect = [ErrorCause("script", "unknown", None, [])]

            with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
                self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
                response = self.client.post('/snapshot/api/stepresult/', data={'step': 5, 'testCase': 5, 'result': True, 'stacktrace': stacktrace})
                self.assertEqual(201, response.status_code)
                time.sleep(1)
                error_cause_finder_instance.detect_cause.assert_not_called()


