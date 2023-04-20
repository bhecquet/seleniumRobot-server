from pathlib import Path

from dramatiq import get_broker, Worker
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django_dramatiq.test import DramatiqTestCase

from django.conf import settings

from snapshotServer.tests import authenticate_test_client_for_api
import os
import json

class TestFieldDetectorView(APITestCase):

    media_dir = settings.MEDIA_ROOT + os.sep + 'detect'

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
        authenticate_test_client_for_api(self.client)

    def test_detect_fields(self):
        """
        Nominal test
        Check the content of reply for field detection
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'field'})
            self.assertEquals(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))

            # check content of data
            self.assertIsNotNone(data['replyDetection.json.png'])
            self.assertEquals(len(data['replyDetection.json.png']['fields']), 21)
            self.assertEquals(len(data['replyDetection.json.png']['labels']), 11)
            self.assertIsNone(data['error'])
            self.assertEquals(data['version'], "afcc45")

            # check files are copied in "detect" media folder
            self.assertTrue(Path(self.media_dir, 'replyDetection.json.json').is_file())
            self.assertTrue(Path(self.media_dir, 'replyDetection.json.png').is_file())

    def test_detect_fields_no_task(self):
        """
        Check error is raised when no task is provided
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp})
            self.assertEquals(response.status_code, 400)


    def test_detect_fields_wrong_task(self):
        """
        Check error is raised when task name is invalid
        """

        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'foo'})
            self.assertEquals(response.status_code, 400)

    def test_detect_fields_error_in_detection(self):
        """
        Check error is raised when detection fails (no data present)
        """

        with open('snapshotServer/tests/data/replyDetectionNoData.json', 'rb') as fp:
            response = self.client.post(reverse('detect'), data={'image': fp, 'task': 'error'})
            self.assertEquals(response.status_code, 500)
            self.assertEquals(json.loads(response.content.decode('UTF-8')), "Model error in detection")

