import json
from unittest import mock

from django.test import SimpleTestCase

from pdf.controllers.comparison import ComparisonError
from pdf.controllers.comparison.comparison_result import Difference
from pdf.controllers.comparison.mistral_document_annotation_comparator import MistralDocComparator
from pdf.tests import build_pdf, http_response

POST = 'pdf.controllers.comparison.mistral_document_annotation_comparator.requests.post'


@mock.patch('pdf.controllers.comparison.mistral_document_annotation_comparator.preferences.get_preference')
class TestMistralDocComparator(SimpleTestCase):

    @staticmethod
    def _prefs(name):
        return {'MISTRAL_DOC_COMPARISON_SYSTEM_PROMPT': 'system %(page_number_1)s/%(page_number_2)s',
                'MISTRAL_DOC_COMPARISON_DIFFERENCES_PROMPT': 'diff %(page_number_1)s/%(page_number_2)s'}[name]

    @staticmethod
    def _mistral_response(differences):
        annotation = json.dumps({'differences': json.dumps(differences)})
        return http_response(content=json.dumps({'document_annotation': annotation}).encode())

    def test_combine_pdf(self, prefs):
        prefs.side_effect = self._prefs
        nb1, nb2, combined = MistralDocComparator('p').combine_pdf_for_comparison(build_pdf(3), build_pdf(2))
        self.assertEqual((3, 2), (nb1, nb2))
        self.assertEqual(2, len(combined))

    def test_filter_differences(self, prefs):
        prefs.side_effect = self._prefs
        d = Difference(1, 'l', 'd')
        self.assertEqual([d, Difference(2, 'l', 'd')],
                         MistralDocComparator('p')._filter_differences([d, Difference(1, 'l', 'd'), Difference(2, 'l', 'd')]))

    @mock.patch(POST)
    def test_compare(self, post, prefs):
        prefs.side_effect = self._prefs
        post.return_value = self._mistral_response([{'location': 'top', 'details': 'changed'}])

        result = MistralDocComparator('p').compare(build_pdf(2), build_pdf(2))

        self.assertEqual(2, post.call_count)
        self.assertEqual([Difference(1, 'top', 'changed'), Difference(2, 'top', 'changed')], result.differences)

    @mock.patch(POST)
    def test_compare_different_page_count(self, post, prefs):
        prefs.side_effect = self._prefs
        post.return_value = self._mistral_response([])

        result = MistralDocComparator('p').compare(build_pdf(1), build_pdf(2))

        self.assertEqual(1, post.call_count)
        self.assertEqual(Difference(0, 'document', 'First document has 1 pages, second has 2 pages'),
                         result.differences[0])

    @mock.patch(POST)
    def test_compare_timeout(self, post, prefs):
        prefs.side_effect = self._prefs
        post.return_value = http_response(status=408)
        with self.assertRaisesRegex(ComparisonError, 'Timeout'):
            MistralDocComparator('p').compare(build_pdf(), build_pdf())

    @mock.patch(POST)
    def test_compare_http_error(self, post, prefs):
        prefs.side_effect = self._prefs
        post.return_value = http_response(status=500)
        with self.assertRaises(ComparisonError):
            MistralDocComparator('p').compare(build_pdf(), build_pdf())

    @mock.patch(POST)
    def test_compare_invalid_body(self, post, prefs):
        prefs.side_effect = self._prefs
        post.return_value = http_response(content=b'not json')
        with self.assertRaises(ComparisonError):
            MistralDocComparator('p').compare(build_pdf(), build_pdf())
