import logging

from django.db import DatabaseError

from snapshotServer.models import ErrorCauseFromUser


logger = logging.getLogger(__name__)


def find_probable_cause(exception, testCase=None, testStep=None):
    """
    Searches for a known cause associated with a specific exception,
    test case, and test step.

    Returns a dictionary if a usable cause exists.
    Returns None if no cause is found or if the provided data
    does not allow the search to be performed.
    """

    # Exception validation
    if not isinstance(exception, str) or not exception.strip():
        logger.warning(
            "Recherche de cause impossible : exception absente ou invalide."
        )
        return None

    # Remove unnecessary whitespace
    normalized_exception = exception.strip()

    # Test context validation
    if testCase is None or testStep is None:
        logger.warning(
            "Unable to search for a cause: incomplete context. "
            "exception='%s', testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )
        return None

    try:
        # Exact search by exception, test case, and test step
        queryset = (
            ErrorCauseFromUser.objects
            .filter(
                exception=normalized_exception,
                testCase=testCase,
                testStep=testStep,
                comment__isnull=False
            )
            .exclude(comment__exact="")
            .order_by("-id")
        )

        number_of_entries = queryset.count()

        # No knowledge entry found
        if number_of_entries == 0:
            logger.debug(
                "No known cause found for exception='%s', "
                "testCase=%s, testStep=%s",
                normalized_exception,
                testCase.id,
                testStep.id
            )
            return None

        # Multiple entries exist for the same context
        if number_of_entries > 1:
            logger.error(
                "Knowledge base inconsistency: "
                "%s causes found for exception='%s', "
                "testCase=%s, testStep=%s. "
                "The most recent cause will be used.",
                number_of_entries,
                normalized_exception,
                testCase.id,
                testStep.id
            )

        # Thanks to order_by("-id"), the most recent entry is selected
        entry = queryset.first()

        if entry is None:
            return None

        # Additional comment validation
        cause = entry.comment.strip()

        if not cause:
            logger.warning(
                "Knowledge entry with id=%s has an empty comment.",
                entry.id
            )
            return None

        logger.debug(
            "Known cause found: id=%s, type=%s, "
            "testCase=%s, testStep=%s",
            entry.id,
            entry.type,
            testCase.id,
            testStep.id
        )

        return {
            "cause": cause,
            "type": entry.type,
            "knowledgeId": entry.id,
            "count": 1,
            "total": number_of_entries
        }

    except DatabaseError:
        logger.exception(
            "Database error while searching for a cause: "
            "exception='%s', testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )

        # The report must continue to be displayed even if the
        # knowledge base is temporarily unavailable.
        return None

    except Exception:
        logger.exception(
            "Unexpected error while analyzing the knowledge base: "
            "exception='%s', testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )

        return None