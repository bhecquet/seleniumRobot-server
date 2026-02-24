from collections import namedtuple
from enum import StrEnum, auto
from typing import Optional

AnalysisDetails = namedtuple('AnalysisDetails', [
    'details',
    'analysis_error'])



class Cause(StrEnum):
    SCRIPT = auto()
    APPLICATION = auto()
    ENVIRONMENT = auto()
    UNKNOWN = auto()

class Reason(StrEnum):
    # application
    STEP_ASSERTION_ERROR = auto()
    SCENARIO_ASSERTION_ERROR = auto()
    ERROR_MESSAGE = auto()
    UNKNOWN_PAGE = auto()
    JAVASCRIPT_ERROR = auto()
    NETWORK_ERROR = auto()

    # environment
    NETWORK_SLOWNESS = auto()

    # script
    BAD_LOCATOR = auto()

    UNKNOWN = auto()

class ErrorCause:
    def __init__(self, cause: Cause, why: Reason, information: str, analysis_errors: Optional[list]):
        """

        :param cause:           the probable cause of the error (application, scripting, tool, environment
        :param why:             what guided us to the probable cause (error message, JS errors, missing field, ...)
        :param information:     additional information related to "why"
        :param analysis_errors: list of error messages during analysis
        """
        self.cause = cause
        self.why= why
        self.information = information
        self.analysis_errors = analysis_errors
