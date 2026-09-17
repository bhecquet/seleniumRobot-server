'''
Tests for snapshotServer.utils.har_analyzer
'''
import json
from pathlib import Path

import django.test

from snapshotServer.utils.har_analyzer import get_network_info_per_page


class TestHarAnalyzer(django.test.TestCase):

    data_dir = Path('snapshotServer/tests/data/')
    har_file = data_dir / 'test_average_time.har'
    network_errors_har_file = data_dir / 'test_network_errors.har'

    def test_network_info_per_page_from_path(self):
        """
        Average time should only take XHR / JS / HTML / image requests into account, and be grouped by page.
        As all requests are successful, no error should be reported
        """
        result = get_network_info_per_page(self.har_file)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'times': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500}, 'errors': []},
            # negative values are ignored
            'Step 2 with args(bar,)': {'times': {'image': 40, 'xhr': 300}, 'errors': []},
            'Step 3 with args(bar,foo)': {'times': {'image': 52}, 'errors': []}})

    def test_network_info_per_page_from_dict(self):
        """
        An already parsed HAR dict should also be accepted
        """
        with open(self.har_file, 'r') as f:
            har = json.load(f)

        result = get_network_info_per_page(har)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'times': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500}, 'errors': []},
            'Step 2 with args(bar,)': {'times': {'image': 40, 'xhr': 300}, 'errors': []},
            'Step 3 with args(bar,foo)': {'times': {'image': 52}, 'errors': []}
        })

    def test_network_info_per_page_from_bytes(self):
        """
        Raw file content (bytes) should also be accepted
        """
        with open(self.har_file, 'rb') as f:
            content = f.read()

        result = get_network_info_per_page(content)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {'times': {'image': 30, 'js': 55, 'xhr': 150, 'html': 500}, 'errors': []},
            'Step 2 with args(bar,)': {'times': {'image': 40, 'xhr': 300}, 'errors': []},
            'Step 3 with args(bar,foo)': {'times': {'image': 52}, 'errors': []}
        })

    def test_page_without_matching_request_or_error_is_omitted(self):
        """
        Pages that only contain non XHR/JS/HTML/image requests, and no error, should not appear in the result
        """
        har = {
            'log': {
                'pages': [{'id': 'page_1', 'title': 'only css'}],
                'entries': [
                    {'pageref': 'page_1', '_resourceType': 'stylesheet', 'time': 100,
                     'request': {'headers': []},
                     'response': {'status': 200, 'statusText': 'OK', 'content': {'mimeType': 'text/css'}}},
                ]
            }
        }
        result = get_network_info_per_page(har)
        self.assertEqual(result, {})

    def test_empty_har(self):
        har = {}

        result = get_network_info_per_page(har)
        self.assertEqual(result, {})

    def test_network_info_per_page_with_errors(self):
        """
        Requests without any response, and requests whose response has a 4xx or 5xx status code, should be
        reported as network errors on the page they belong to. Successful requests (2xx / 3xx) should not be
        reported as errors
        """
        result = get_network_info_per_page(self.network_errors_har_file)
        self.assertEqual(result, {
            'Step 1 with args(foo,)': {
                'times': {},
                'errors': [
                    {'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'},
                    {'url': 'https://myapp/api/save', 'status': 500, 'statusText': 'Internal Server Error'},
                ]
            },
            'Step 2 with args(bar,)': {
                'times': {},
                'errors': [
                    {'url': 'https://myapp/api/timeout', 'status': None, 'statusText': None},
                    {'url': 'https://myapp/api/aborted', 'status': None, 'statusText': None},
                ]
            }
        })

    def test_network_info_per_page_with_errors_from_dict(self):
        """
        An already parsed HAR dict should also be accepted
        """
        with open(self.network_errors_har_file, 'r') as f:
            har = json.load(f)

        result = get_network_info_per_page(har)
        self.assertEqual(len(result['Step 1 with args(foo,)']['errors']), 2)
        self.assertEqual(len(result['Step 2 with args(bar,)']['errors']), 2)

    def test_network_info_per_page_no_error(self):
        """
        When all requests are successful, no error should be reported for the page
        """
        har = {
            'log': {
                'pages': [{'id': 'page_1', 'title': 'all good'}],
                'entries': [
                    {'pageref': 'page_1', 'time': 10, 'request': {'headers': [], 'url': 'https://myapp/api/data'},
                     'response': {'status': 200, 'statusText': 'OK', 'content': {'mimeType': 'application/json'}}},
                    {'pageref': 'page_1', 'time': 20, 'request': {'headers': [], 'url': 'https://myapp/redirect'},
                     'response': {'status': 301, 'statusText': 'Moved Permanently', 'content': {'mimeType': 'application/json'}}},
                ]
            }
        }
        result = get_network_info_per_page(har)
        self.assertEqual(result, {'all good': {'times': {'xhr': 15}, 'errors': []}})

    def test_network_info_per_page_unknown_page(self):
        """
        When a request references a page that is not declared in the 'pages' section, the pageref itself is
        used as page name
        """
        har = {
            'log': {
                'pages': [],
                'entries': [
                    {'pageref': 'unknown_page', 'request': {'url': 'https://myapp/api/data'},
                     'response': {'status': 404, 'statusText': 'Not Found'}},
                ]
            }
        }
        result = get_network_info_per_page(har)
        self.assertEqual(result, {
            'unknown_page': {'times': {}, 'errors': [{'url': 'https://myapp/api/data', 'status': 404, 'statusText': 'Not Found'}]}
        })

    def test_network_info_per_page_only_errors_no_timed_requests(self):
        """
        A page containing only requests in error (no successful timed requests) should still appear in the
        result, with an empty 'times' dict
        """
        har = {
            'log': {
                'pages': [{'id': 'page_1', 'title': 'broken page'}],
                'entries': [
                    {'pageref': 'page_1', 'request': {'headers': [], 'url': 'https://myapp/api/aborted'}},
                ]
            }
        }
        result = get_network_info_per_page(har)
        self.assertEqual(result, {
            'broken page': {'times': {}, 'errors': [{'url': 'https://myapp/api/aborted', 'status': None, 'statusText': None}]}
        })
