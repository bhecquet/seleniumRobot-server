import json
from typing import Optional

from snapshotServer.controllers.error_cause import AnalysisDetails

class NetworkAnalysisDetails:

    def __init__(self, errors: list, analysis_error: Optional[str]):
        self.errors = errors
        self.analysis_error = analysis_error


class NetworkErrorCauseFinder:

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session


    def has_network_errors(self) -> NetworkAnalysisDetails:
        """
        Check in HAR file of the current test if some error occurred in the current page or the previous one
        :return:
        """
        return NetworkAnalysisDetails([], None)

    def has_network_slowness(self) -> NetworkAnalysisDetails:
        """
        Check in HAR file of the current test if some slowness occurred in the current page or the previous one
        :return:
        """
        return NetworkAnalysisDetails([], None)