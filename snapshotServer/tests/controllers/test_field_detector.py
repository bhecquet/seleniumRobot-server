'''
Created on 11 mai 2023

@author: bhecquet
'''
import os

from django.conf import settings
from django.test import TestCase
from snapshotServer.controllers.FieldDetector import FieldDetector
from dramatiq.broker import get_broker
from dramatiq.worker import Worker
from pathlib import Path
from django.test.utils import override_settings
import time


@override_settings(FIELD_DETECTOR_ENABLED='True')
class TestFieldDetector(TestCase):
    
    fixtures = ['snapshotServer.yaml']
    detect_dir = settings.MEDIA_ROOT + os.sep + 'detect'
    
    def setUp(self):
        super().setUp()
         
        for f in os.listdir(self.detect_dir):
            if f.startswith('replyDetection'):
                os.remove(self.detect_dir + os.sep + f)
                
    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()

    def test_detect_fields(self):
        """
        Test field detection when field detector is enabled
        """
        
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            detection_data = FieldDetector().detect(fp.read(), 'replyDetection.json.png', 'field_processor', 1.0)
            self.assertEqual(len(detection_data['fields']), 21)
            self.assertEqual(len(detection_data['labels']), 11)
            self.assertEqual(detection_data['fileName'], 'replyDetection.json.png')
            self.assertIsNone(detection_data['error'])
            self.assertEqual(detection_data['version'], "afcc45")
            
            # check content to see if merging between text and fields is properly done
            self.assertEqual(detection_data['fields'][4]['text'], "Full Name")
            
            # check files are there
            self.assertTrue(Path(self.detect_dir, 'replyDetection.json.png').exists())
            self.assertTrue(Path(self.detect_dir, 'replyDetection.json.json').exists())
            
    def test_clean_detected_files(self):
        """
        Test we clean detected files
        """
        
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            FieldDetector().detect(fp.read(), 'replyDetection.json.png', 'field_processor', 1.0)

            # check files are there
            self.assertTrue(Path(self.detect_dir, 'replyDetection.json.png').exists())
            self.assertTrue(Path(self.detect_dir, 'replyDetection.json.json').exists())
        
        try:
            FieldDetector.CLEAN_EVERY_SECONDS = 0    
            FieldDetector.DELETE_AFTER = 0    
            with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
                FieldDetector().detect(fp.read(), 'replyDetection2.json.png', 'field_processor', 1.0)
                time.sleep(1)
                
                # check previous files are removed
                self.assertFalse(Path(self.detect_dir, 'replyDetection.json.png').exists())
                self.assertFalse(Path(self.detect_dir, 'replyDetection.json.json').exists())
                self.assertTrue(Path(self.detect_dir, 'replyDetection2.json.png').exists())
                self.assertTrue(Path(self.detect_dir, 'replyDetection2.json.json').exists())
        finally:
            # reset as it's modified in test
            FieldDetector.DELETE_AFTER = 60 * 60 * 24 * 30
            FieldDetector.CLEAN_EVERY_SECONDS = 60 * 60 * 24

    
    @override_settings(FIELD_DETECTOR_ENABLED='False')
    def test_detect_fields_disabled(self):
        """
        Test field detection when field detector is disabled
        """
        
        with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
            detection_data = FieldDetector().detect(fp.read(), 'replyDetection.json.png', 'field_processor', 1.0)
            self.assertEqual(detection_data, {'error': 'Field detector disabled'})

    def test_detect_fields_error_in_detection(self):
        """
        When field detection fails, check we return an error
        """
        
        with open('snapshotServer/tests/data/replyDetectionNoData.json', 'rb') as fp:
            detection_data = FieldDetector().detect(fp.read(), 'replyDetection.json.png', 'field_processor', 1.0)
            self.assertEqual(detection_data, {'error': 'Model error in detection'})

    def test_detect_fields_error_timeout(self):
        """
        When field detection fails due to timeout, error is raised
        """
        
        detection_data = FieldDetector().detect(b'exception:ResultTimeout', 'replyDetection.json.png', 'field_processor', 1.0)
        self.assertEqual(detection_data, {'error': 'Timeout waiting for computation'})

    def test_correlate_text_and_fields(self):
        """
        Check matching of field with label
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 10,
                        "width": 70,
                        "height": 16,
                        "text": "Join Us",
                        "right": 80,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 10,
                "right": 200,
                "class_name": "field_with_label",
                "text": None,
                "related_field": {
                    "class_id": 0,
                    "top": 1,
                    "bottom": 19,
                    "left": 100,
                    "right": 190,
                    "class_name": "field",
                    "text": None,
                    "related_field": None,
                    "with_label": False,
                    "width": 90,
                    "height": 18
                },
                "with_label": True,
                "width": 190,
                "height": 24
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertEqual(fields[0]['text'], 'Join Us')

    def test_correlate_text_and_fields_match_class_error(self):
        """
        matching will be done as field is an error field and we always match if position are correct
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 10,
                        "width": 70,
                        "height": 16,
                        "text": "Join Us",
                        "right": 80,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 10,
                "right": 200,
                "class_name": "error_field",
                "text": None,
                "with_label": False,
                "width": 190,
                "height": 24
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertEqual(fields[0]['text'], 'Join Us')
        
    def test_correlate_text_and_fields_no_match_class_no_field(self):
        """
        No matching will be done as field is not referenced as a "field_with_label"
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 10,
                        "width": 70,
                        "height": 16,
                        "text": "Join Us",
                        "right": 80,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 10,
                "right": 200,
                "class_name": "field",
                "text": None,
                "with_label": False,
                "width": 190,
                "height": 24
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertIsNone(fields[0]['text'])
        
    def test_correlate_text_and_fields_no_match(self):
        """
        Matching not done, field is outside of label box
        """
        labels = {'Join Us': {
                        "top": 10,
                        "left": 10,
                        "width": 20,
                        "height": 20,
                        "text": "Join Us",
                        "right": 30,
                        "bottom": 30
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 10,
                "right": 200,
                "class_name": "field_with_label",
                "text": None,
                "related_field": {
                    "class_id": 0,
                    "top": 1,
                    "bottom": 19,
                    "left": 100,
                    "right": 190,
                    "class_name": "field",
                    "text": None,
                    "related_field": None,
                    "with_label": False,
                    "width": 90,
                    "height": 18
                },
                "with_label": True,
                "width": 190,
                "height": 20
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertIsNone(fields[0]['text'])
        
    def test_correlate_text_and_fields_no_match2(self):
        """
        Matching not done, field is outside of label box (label on the top)
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 10,
                        "width": 20,
                        "height": 16,
                        "text": "Join Us",
                        "right": 30,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 13,
                "bottom": 33,
                "left": 10,
                "right": 200,
                "class_name": "field_with_label",
                "text": None,
                "related_field": {
                    "class_id": 0,
                    "top": 1,
                    "bottom": 19,
                    "left": 100,
                    "right": 190,
                    "class_name": "field",
                    "text": None,
                    "related_field": None,
                    "with_label": False,
                    "width": 90,
                    "height": 18
                },
                "with_label": True,
                "width": 190,
                "height": 20
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertIsNone(fields[0]['text'])
        
    def test_correlate_text_and_fields_no_match3(self):
        """
        Matching not done, field is outside of label box (label on the right)
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 190,
                        "width": 20,
                        "height": 16,
                        "text": "Join Us",
                        "right": 210,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 10,
                "right": 200,
                "class_name": "field_with_label",
                "text": None,
                "related_field": {
                    "class_id": 0,
                    "top": 1,
                    "bottom": 19,
                    "left": 100,
                    "right": 190,
                    "class_name": "field",
                    "text": None,
                    "related_field": None,
                    "with_label": False,
                    "width": 90,
                    "height": 18
                },
                "with_label": True,
                "width": 190,
                "height": 24
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertIsNone(fields[0]['text'])
        
    def test_correlate_text_and_fields_no_match4(self):
        """
        Matching not done, field is outside of label box (label on the left)
        """
        labels = {'Join Us': {
                        "top": 5,
                        "left": 10,
                        "width": 70,
                        "height": 16,
                        "text": "Join Us",
                        "right": 80,
                        "bottom": 21
                    },
                }
        
        fields = [
            {
                "class_id": 4,
                "top": 0,
                "bottom": 20,
                "left": 50,
                "right": 200,
                "class_name": "field_with_label",
                "text": None,
                "related_field": {
                    "class_id": 0,
                    "top": 1,
                    "bottom": 19,
                    "left": 100,
                    "right": 190,
                    "class_name": "field",
                    "text": None,
                    "related_field": None,
                    "with_label": False,
                    "width": 90,
                    "height": 18
                },
                "with_label": True,
                "width": 150,
                "height": 24
            },
           
            ]
        
        # text has been added to field
        FieldDetector().correlate_text_and_fields(labels, fields)
        self.assertIsNone(fields[0]['text'])
        