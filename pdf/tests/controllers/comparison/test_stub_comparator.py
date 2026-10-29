import json

from django.test import SimpleTestCase

from pdf.controllers.comparison.comparison_result import Difference
from pdf.controllers.comparison.stub_comparator import StubComparator
from pdf.tests import build_pdf


class TestStubComparator(SimpleTestCase):

    def test_compare(self):
        """RG-STB-01: fixed result"""
        result = StubComparator('').compare(build_pdf(), build_pdf())
        self.assertEqual([Difference(1, 'first part', 'Amount is different')], result.differences)
        json.loads(result.serialize()['full_response'])
