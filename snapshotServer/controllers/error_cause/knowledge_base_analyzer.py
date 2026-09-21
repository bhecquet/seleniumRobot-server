import logging

from django.db import DatabaseError

from snapshotServer.models import ErrorCauseFromUser


logger = logging.getLogger(__name__)


def find_probable_cause(exception, testCase=None, testStep=None):
    """
    Recherche une cause connue pour une exception, un test
    et une étape précise.

    Retourne un dictionnaire si une cause exploitable existe.
    Retourne None si aucune cause n'est trouvée ou si les
    données reçues ne permettent pas d'effectuer la recherche.
    """

    # Vérification de l'exception
    if not isinstance(exception, str) or not exception.strip():
        logger.warning(
            "Recherche de cause impossible : exception absente ou invalide."
        )
        return None

    # Suppression des espaces inutiles
    normalized_exception = exception.strip()

    # Vérification du contexte du test
    if testCase is None or testStep is None:
        logger.warning(
            "Recherche de cause impossible : contexte incomplet. "
            "exception='%s', testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )
        return None

    try:
        # Recherche exacte par exception, test et étape
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

        # Aucune connaissance trouvée
        if number_of_entries == 0:
            logger.debug(
                "Aucune cause connue pour exception='%s', "
                "testCase=%s, testStep=%s",
                normalized_exception,
                testCase.id,
                testStep.id
            )
            return None

        # Plusieurs entrées existent pour le même contexte
        if number_of_entries > 1:
            logger.error(
                "Incohérence dans la base de connaissance : "
                "%s causes trouvées pour exception='%s', "
                "testCase=%s, testStep=%s. "
                "La cause la plus récente sera utilisée.",
                number_of_entries,
                normalized_exception,
                testCase.id,
                testStep.id
            )

        # Grâce à order_by("-id"), la plus récente est sélectionnée
        entry = queryset.first()

        if entry is None:
            return None

        # Vérification complémentaire du commentaire
        cause = entry.comment.strip()

        if not cause:
            logger.warning(
                "La connaissance id=%s possède un commentaire vide.",
                entry.id
            )
            return None

        logger.debug(
            "Cause connue trouvée : id=%s, type=%s, "
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
            "Erreur de base de données pendant la recherche "
            "d'une cause : exception='%s', testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )

        # Le rapport doit continuer à s'afficher même si la
        # base de connaissance est temporairement indisponible.
        return None

    except Exception:
        logger.exception(
            "Erreur inattendue pendant l'analyse de la base "
            "de connaissance : exception='%s', "
            "testCase=%s, testStep=%s",
            normalized_exception,
            getattr(testCase, "id", None),
            getattr(testStep, "id", None)
        )

        return None