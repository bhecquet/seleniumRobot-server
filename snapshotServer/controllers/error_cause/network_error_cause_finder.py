import json
from snapshotServer.controllers.error_cause import AnalysisDetails


class NetworkErrorCauseFinder:

    def __init__(self, test_case_in_session):
        self.test_case_in_session = test_case_in_session


    def has_network_errors(self) -> AnalysisDetails:
        """
        Check in HAR file of the current test if some error occurred in the current page or the previous one
        :return:
        """
        return AnalysisDetails([], None)

    def has_network_slowness(self) -> AnalysisDetails:
        """
        Check in HAR file of the current test if some slowness occurred in the current page or the previous one
        :return:
        """
        return AnalysisDetails([], None)