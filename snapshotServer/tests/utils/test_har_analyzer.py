'''
Tests for snapshotServer.utils.har_analyzer
'''
import json
from pathlib import Path

import django.test

from snapshotServer.utils.har_analyzer import get_average_request_time_per_page


class TestHarAnalyzer(django.test.TestCase):

    data_dir = Path('snapshotServer/tests/data/')
    har_file = data_dir / 'test_average_time.har'

    def test_average_time_per_page_from_path(self):
        """
        Average time should only take XHR / JS / image requests into account, and be grouped by page
        """
        result = get_average_request_time_per_page(self.har_file)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500},
            # negative values are ignored
            'Step 2 with args(bar,)': {'image': 40, 'xhr': 300},
            'Step 3 with args(bar,foo)': {'image': 52}})

    def test_average_time_per_page_from_dict(self):
        """
        An already parsed HAR dict should also be accepted
        """
        with open(self.har_file, 'r') as f:
            har = json.load(f)

        result = get_average_request_time_per_page(har)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500},
            'Step 2 with args(bar,)': {'image': 40, 'xhr': 300},
            'Step 3 with args(bar,foo)': {'image': 52}
        })

    def test_average_time_per_page_from_bytes(self):
        """
        Raw file content (bytes) should also be accepted
        """
        with open(self.har_file, 'rb') as f:
            content = f.read()

        result = get_average_request_time_per_page(content)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500},
            'Step 2 with args(bar,)': {'image': 40, 'xhr': 300},
            'Step 3 with args(bar,foo)': {'image': 52}
        })

    def test_page_without_matching_request_is_omitted(self):
        """
        Pages that only contain non XHR/JS/image requests should not appear in the result
        """
        har = {
            'log': {
                'pages': [{'id': 'page_1', 'title': 'only css'}],
                'entries': [
                    {'pageref': 'page_1', '_resourceType': 'stylesheet', 'time': 100,
                     'request': {'headers': []}, 'response': {'content': {'mimeType': 'text/css'}}},
                ]
            }
        }
        result = get_average_request_time_per_page(har)
        self.assertEqual(result, {})

    def test_empty_har(self):
        har = {}

        result = get_average_request_time_per_page(har)
        self.assertEqual(result, {})
