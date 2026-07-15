from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference


class StubComparator():

    def __init__(self, system_prompt):
        pass

    def compare(self, pdf1, pdf2) -> ComparisonResult:
        """Simulate a PDF comparison by returning a fixed result."""

        differences = [Difference(1, "first part", "Amount is different")]
        return ComparisonResult(differences)