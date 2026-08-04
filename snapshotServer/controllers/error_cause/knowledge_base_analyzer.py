from django.db.models import Count
from snapshotServer.models import ErrorCauseFromUser


def find_probable_cause(exception, testCase=None, testStep=None):


    entry = ErrorCauseFromUser.objects.filter(
        exception=exception,
        testCase=testCase,
        testStep=testStep
    ).first()

    if not entry:
        return None

    return {
        "cause": entry.commentaire,
        "count": 1,
        "total": 1
    }


