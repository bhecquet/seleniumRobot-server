import base64
import datetime
import json
import os
from pathlib import Path
import time

from django.conf import settings
from django.test.utils import override_settings
from django_dramatiq.test import DramatiqTestCase
from dramatiq import get_broker, Worker
import pytz
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from snapshotServer.models import TestCase, Application, TestStep, TestSession, \
    Version, TestEnvironment, TestCaseInSession, StepResult, StepReference
from snapshotServer.tests import authenticate_test_client_for_api
import unittest


@override_settings(FIELD_DETECTOR_ENABLED='True')
class TestFieldDetectorView(APITransactionTestCase): # use APITransactionTestCase to avoid 'database table is locked'

    media_dir = settings.MEDIA_ROOT + os.sep + 'detect'
    fixtures = ['snapshotServer.yaml']

    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()


    def setUp(self):
        print(unittest.TestCase.id(self))
        authenticate_test_client_for_api(self.client)
        
        self.testCase = TestCase(name='test upload', application=Application.objects.get(id=1))
        self.testCase.save()
        self.step1 = TestStep.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="8888", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.sr1 = StepResult(step=self.step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        
        self.session_same_env = TestSession(sessionId="8889", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_same_env.save()
        self.tcs_same_env = TestCaseInSession(testCase=self.testCase, session=self.session_same_env)
        self.tcs_same_env.save()
        self.step_result_same_env = StepResult(step=self.step1, testCase=self.tcs_same_env, result=True)
        self.step_result_same_env.save()

    def test_detect_fields(self):
        """
        Nominal test
        Check the content of reply for field detection
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))

            # check content of data
            self.assertEqual(len(data['fields']), 21)
            self.assertEqual(len(data['labels']), 11)
            self.assertEqual(data['fileName'], 'replyDetection.json.png')
            self.assertIsNone(data['error'])
            self.assertEqual(data['version'], "afcc45")

            # check files are copied in "detect" media folder
            self.assertTrue(Path(self.media_dir, 'replyDetection.json.json').is_file())
            self.assertTrue(Path(self.media_dir, 'replyDetection.json.png').is_file())

    @override_settings(FIELD_DETECTOR_ENABLED='False')
    def test_detect_fields_disabled(self):
        """
        Nominal test
        Check the content of reply for field detection
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 500)

    def test_detect_fields_no_task(self):
        """
        Check error is raised when no task is provided
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp})
            self.assertEqual(response.status_code, 400)


    def test_detect_fields_wrong_task(self):
        """
        Check error is raised when task name is invalid
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'foo'})
            self.assertEqual(response.status_code, 400)

    def test_detect_fields_error_in_detection(self):
        """
        Check error is raised when detection fails (no data present)
        """

        with open('snapshotServer/tests/data/replyDetectionNoData.json', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'error'})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(json.loads(response.content.decode('UTF-8')), "Model error in detection")

    def test_get_fields_from_previous_detection_format_json(self):
        """
        Check it's possible to retrieve the detection result of a previously analyzed picture as a json file
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            data = response.content.decode('UTF-8')
            
        response = self.client.get(reverse('detect'), data={'image': 'replyDetection.json.png', 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        data2 = response.content.decode('UTF-8')
        
        # check both responses are the same (limit to beginning is enough to check we get the same information and we won't be bohered by file encoding)
        self.assertEqual(data.replace(' ', '')[:300], data2.replace(' ', '')[:300])

    def test_get_fields_from_previous_detection_unknown_image(self):
        """
        Check error is raised if provided image name is unknown
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            data = response.content.decode('UTF-8')
            
        response = self.client.get(reverse('detect'), data={'image': 'other_image.png', 'output': 'json'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b'"image \'other_image.png\' not found"')

    def test_get_fields_from_previous_detection_format_image(self):
        """
        Check it's possible to retrieve the detection image of a previously analyzed picture as an image
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            
        response = self.client.get(reverse('detect'), data={'image': 'replyDetection.json.png', 'output': 'image'})
        self.assertEqual(response.status_code, 200)
        data2 = response.content
        
        # check we get image file
        self.assertEqual(data2[:15], b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00')
        
    def test_get_fields_from_step_result_format_json(self):
        """
        Check it's possible to retrieve the detection result of a step reference, given a step result id
        """
        
        # record a step reference, computing should be done at this step
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            time.sleep(1) # wait field computing
            
            # check computing has been done
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            self.assertIsNotNone(uploaded_reference_1.field_detection_data)
            self.assertIsNotNone(uploaded_reference_1.field_detection_date)
            self.assertEqual(uploaded_reference_1.field_detection_version, 'afcc45')
            

        # get field detection result
        response = self.client.get(reverse('detect'), data={'stepResultId': self.step_result_same_env.id, 'version': 'afcc45', 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(data['version'], 'afcc45')
        self.assertEquals(data['fileName'], Path(uploaded_reference_1.field_detection_data.file.name).with_suffix('.png').name) # check data are get from the computed file on first submission
        
    def test_get_fields_from_step_result_format_json_no_previous_field_computation(self):
        """
        If step reference does not have field_detection data (due to bug, computing failure, ...), check computing is retried when we access it
        """
        
        # record a step reference, computing should be done at this step
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            time.sleep(1) # wait field computing
            
            # remove computing information to force recomputing
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            uploaded_reference_1.field_detection_data = None
            uploaded_reference_1.field_detection_date = None
            uploaded_reference_1.field_detection_version = ""
            uploaded_reference_1.save()

        # get field detection result
        response = self.client.get(reverse('detect'), data={'stepResultId': self.step_result_same_env.id, 'version': 'afcc45', 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        
        # check computing has been done when getting result
        uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
        self.assertIsNotNone(uploaded_reference_1.field_detection_data)
        self.assertIsNotNone(uploaded_reference_1.field_detection_date)
        self.assertEqual(uploaded_reference_1.field_detection_version, 'afcc45')
        
    def test_get_fields_from_step_result_format_json_wrong_model_version(self):
        """
        If step reference has a field_detector_version different from what is provided, recompute, assuming a new model version has been published
        """
        
        # record a step reference, computing should be done at this step
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            time.sleep(1) # wait field computing
            
            # remove computing information to force recomputing
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            uploaded_reference_1.field_detection_version = "aaaaa"
            uploaded_reference_1.save()

        # get field detection result
        response = self.client.get(reverse('detect'), data={'stepResultId': self.step_result_same_env.id, 'version': 'afcc45', 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(data['version'], 'afcc45')
        
        # check computing has re-done
        uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
        self.assertIsNotNone(uploaded_reference_1.field_detection_data)
        self.assertIsNotNone(uploaded_reference_1.field_detection_date)
        self.assertEqual(uploaded_reference_1.field_detection_version, 'afcc45')

        
    def test_get_fields_from_step_result_format_image(self):
        """
        Check it's possible to retrieve the detection image of a step reference, given a step result id
        """
        
        # record a step reference, computing should be done at this step
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            time.sleep(1) # wait field computing
            
            # chech computing has been done
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            self.assertIsNotNone(uploaded_reference_1.field_detection_data)
            self.assertIsNotNone(uploaded_reference_1.field_detection_date)
            self.assertEqual(uploaded_reference_1.field_detection_version, 'afcc45')
            

        # get field detection result
        response = self.client.get(reverse('detect'), data={'stepResultId': self.step_result_same_env.id, 'version': 'afcc45', 'output': 'image'})
        self.assertEqual(response.status_code, 200)
        data2 = response.content
        
        # check we get image file
        self.assertEqual(data2[:15], b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00')
        
    
    def test_get_fields_wrong_output(self):
        """
        output format should be 'image' or 'json' only
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            
        response = self.client.get(reverse('detect'), data={'image': 'replyDetection.json.png', 'output': 'foo'})
        self.assertEqual(response.status_code, 400)
    
    def test_get_fields_missing_output(self):
        """
        output param is mandatory
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            
        response = self.client.get(reverse('detect'), data={'image': 'replyDetection.json.png'})
        self.assertEqual(response.status_code, 400)
        
    
    def test_get_fields_missing_step_result_id_and_image(self):
        """
        'image' or 'step_result_id' must be provided
        """
        
        # trigger detection
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEqual(response.status_code, 200)
            
        response = self.client.get(reverse('detect'), data={'output': 'json'})
        self.assertEqual(response.status_code, 400)