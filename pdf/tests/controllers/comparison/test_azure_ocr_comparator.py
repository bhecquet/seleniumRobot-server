import json
from unittest import mock

from django.test import SimpleTestCase

from pdf.controllers.comparison import ComparisonError
from pdf.controllers.comparison.azure_ocr_comparator import AzureOcrComparator, format_details_for_content_difference
from pdf.tests import build_pdf, http_response

GET = 'pdf.controllers.comparison.azure_ocr_comparator.requests.get'
POST = 'pdf.controllers.comparison.azure_ocr_comparator.requests.post'


class TestAzureOcrComparator(SimpleTestCase):

    def _auth_responses(self):
        return [http_response(json_data={'access_token': 'kv'}),
                http_response(json_data={'value': 'apikey'}),
                http_response(json_data={'access_token': 'backend'})]

    @mock.patch(GET)
    def test_authenticate(self, get):
        """RG-AZR-01: 3-step authentication"""
        get.side_effect = self._auth_responses()
        self.assertEqual(('apikey', 'backend'), AzureOcrComparator('')._authenticate())

    @mock.patch(GET)
    def test_authenticate_keyvault_token_error(self, get):
        """RG-AZR-01: HTTP code other than 200 at step 1"""
        get.return_value = http_response(status=401)
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(GET)
    def test_authenticate_missing_token(self, get):
        """RG-AZR-01: missing token at step 1"""
        get.return_value = http_response(json_data={})
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(GET)
    def test_authenticate_keyvault_error(self, get):
        """RG-AZR-01: HTTP code other than 200 at step 2"""
        get.side_effect = [http_response(json_data={'access_token': 'kv'}), http_response(status=500)]
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(GET)
    def test_authenticate_missing_api_key(self, get):
        """RG-AZR-01: missing API key at step 2"""
        get.side_effect = [http_response(json_data={'access_token': 'kv'}), http_response(json_data={})]
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(GET)
    def test_authenticate_backend_error(self, get):
        """RG-AZR-01: HTTP code other than 200 at step 3"""
        get.side_effect = self._auth_responses()[:2] + [http_response(status=403)]
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(GET)
    def test_authenticate_missing_backend_token(self, get):
        """RG-AZR-01: missing backend token at step 3"""
        get.side_effect = self._auth_responses()[:2] + [http_response(json_data={})]
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('')._authenticate()

    @mock.patch(POST)
    @mock.patch(GET)
    def test_compare(self, get, post):
        """RG-AZR-02, RG-AZR-03: files sent with the subscription key, differences converted"""
        get.side_effect = self._auth_responses()
        body = {'content_differences': [{'page': 2, 'section': 'S', 'difference_type': 'changed',
                                         'field': 'f', 'document_1': 'a', 'document_2': 'b'}]}
        post.return_value = http_response(json_data=body, content=json.dumps(body).encode())

        result = AzureOcrComparator('').compare(build_pdf(), build_pdf())

        self.assertEqual(1, len(result.differences))
        self.assertEqual(2, result.differences[0].page)
        self.assertEqual('S', result.differences[0].location)
        self.assertIn("doc2: 'b'", result.differences[0].details)
        self.assertEqual('apikey', post.call_args.kwargs['headers']['ocp-apim-subscription-key'])

    @mock.patch(POST)
    @mock.patch(GET)
    def test_compare_http_error(self, get, post):
        """RG-AZR-02: HTTP code other than 200 on comparison"""
        get.side_effect = self._auth_responses()
        post.return_value = http_response(status=500)
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('').compare(build_pdf(), build_pdf())

    @mock.patch(POST)
    @mock.patch(GET)
    def test_compare_invalid_body(self, get, post):
        """RG-AZR-03: malformed response"""
        get.side_effect = self._auth_responses()
        post.return_value = http_response(json_data={'other': 1})
        with self.assertRaises(ComparisonError):
            AzureOcrComparator('').compare(build_pdf(), build_pdf())

    def test_format_details(self):
        """RG-AZR-03: formatting of a difference details"""
        details = format_details_for_content_difference({'field': 'x'})
        self.assertIn("field: 'x'", details)
