from django.test import SimpleTestCase

from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference


class TestDifference(SimpleTestCase):

    def test_serialize(self):
        self.assertEqual({'page': 2, 'details': 'd', 'location': 'l'}, Difference(2, 'l', 'd').serialize())

    def test_invalid_page(self):
        self.assertEqual(-1, Difference('N/A', 'l', 'd').page)

    def test_negative_page(self):
        self.assertEqual(0, Difference(-3, 'l', 'd').page)

    def test_equality(self):
        self.assertEqual(Difference(1, 'l', 'd'), Difference(1, 'l', 'd'))
        self.assertNotEqual(Difference(1, 'l', 'd'), Difference(2, 'l', 'd'))


class TestComparisonResult(SimpleTestCase):

    def test_serialize(self):
        result = ComparisonResult([Difference(1, 'l', 'd')], b'{"a": 1}')
        self.assertEqual({'differences': [{'page': 1, 'details': 'd', 'location': 'l'}],
                          'full_response': '{"a": 1}'}, result.serialize())

    def test_default_response(self):
        self.assertEqual('{}', ComparisonResult([]).serialize()['full_response'])
