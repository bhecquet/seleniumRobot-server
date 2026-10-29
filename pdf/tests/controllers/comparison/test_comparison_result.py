from django.test import SimpleTestCase

from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference


class TestDifference(SimpleTestCase):

    def test_serialize(self):
        """RG-DIF-04: difference serialization"""
        self.assertEqual({'page': 2, 'details': 'd', 'location': 'l'}, Difference(2, 'l', 'd').serialize())

    def test_invalid_page(self):
        """RG-DIF-01: non numeric page => -1"""
        self.assertEqual(-1, Difference('N/A', 'l', 'd').page)

    def test_negative_page(self):
        """RG-DIF-01: negative page => 0"""
        self.assertEqual(0, Difference(-3, 'l', 'd').page)

    def test_equality(self):
        """RG-DIF-03: equality on page, details and location"""
        self.assertEqual(Difference(1, 'l', 'd'), Difference(1, 'l', 'd'))
        self.assertNotEqual(Difference(1, 'l', 'd'), Difference(2, 'l', 'd'))


class TestComparisonResult(SimpleTestCase):

    def test_serialize(self):
        """RG-DIF-05: result serialization"""
        result =  ComparisonResult([Difference(1, 'l', 'd')], b'{"a": 1}')
        self.assertEqual({'differences': [{'page': 1, 'details': 'd', 'location': 'l'}],
                          'full_response': '{"a": 1}'}, result.serialize())

    def test_default_response(self):
        """RG-DIF-05: default full response is '{}'"""
        self.assertEqual('{}', ComparisonResult([]).serialize()['full_response'])
