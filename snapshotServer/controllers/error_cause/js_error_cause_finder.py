import json
from datetime import datetime

from snapshotServer.controllers.error_cause import AnalysisDetails
from snapshotServer.models import StepResult, TestStep, File


class JsErrorCauseFinder:

    def __init__(self, test_case_in_session):

        self.test_case_in_session = test_case_in_session

    def has_javascript_errors(self) -> AnalysisDetails:
        """
        Returns the list of javascript errors or empty list if none are seen
        Browser logs are recorded to 'Test end' step
        :return [[logs], <analysis_error_if_any>]
        """
        last_step = StepResult.objects.filter(testCase=self.test_case_in_session, step__name=TestStep.LAST_STEP_NAME)
        failed_step_result = StepResult.objects.filter(testCase=self.test_case_in_session, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')

        if len(last_step) > 0 and len(failed_step_result) > 0:
            last_step = last_step[0]
            failed_step_result = failed_step_result[0]

            try:
                # load details
                last_step_result_details = json.loads(last_step.stacktrace)
                failed_step_result_details = json.loads(failed_step_result.stacktrace)
                for file_info in last_step_result_details['files']:
                    if file_info["name"] == "Browser log file":
                        log_file = File.objects.get(pk=file_info['id'])
                        return self._analyze_javascript_logs(log_file.file.path, failed_step_result_details['timestamp'])

                return AnalysisDetails([], "No browser logs to analyze")
            except Exception as e:
                return AnalysisDetails([], f"Error reading step details for analysis: {str(e)}")

        return AnalysisDetails([], f"No '{TestStep.LAST_STEP_NAME}' step where logs can be found")

    def _analyze_javascript_logs(self, log_file_path: str, failed_step_result_timestamp: int) -> AnalysisDetails:
        """
        Analyze log file, looking for logs that happen after the start of the failed step
        Filtering is done only on "SEVERE" messages
        :param log_file_path:                   path to browser log file
        :param failed_step_result_timestamp:    timestamp in milliseconds
        :return:
        """
        if 'chrome' in self.test_case_in_session.session.browser.lower() or 'edge' in self.test_case_in_session.session.browser.lower():
            logs = []
            try:
                with open(log_file_path, 'r') as log_file:
                    for line in log_file:
                        log_timestamp = datetime.strptime(line.split("]")[0][1:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp() * 1000 # in milliseconds
                        if log_timestamp > failed_step_result_timestamp and "severe" in line.lower():
                            logs.append(line.strip())

                    return AnalysisDetails(logs, None)

            except Exception as e:
                return AnalysisDetails([], "Error reading log file: " + str(e))


        else:
            return AnalysisDetails([], "Only chrome / Edge logs can be analyzed")
