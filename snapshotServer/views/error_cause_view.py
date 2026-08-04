import logging

from django.contrib import messages
from django.db import DatabaseError, transaction
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from snapshotServer.models import ErrorCauseFromUser, TestStep, TestCase


logger = logging.getLogger(__name__)


@require_POST
def save_error_cause(request):

    exception = request.POST.get("exception", "").strip()
    error_message = request.POST.get("errorMessage", "").strip()
    action = request.POST.get("stepName", "").strip()
    commentaire = request.POST.get("commentaire", "").strip()
    cause_type = request.POST.get("cause", "").strip()

    test_step_id = request.POST.get("testStepId")
    test_case_id = request.POST.get("testCaseId")

    redirect_url = request.META.get("HTTP_REFERER", "/")

    # Vérification des données obligatoires
    if not exception:
        messages.error(
            request,
            "Impossible d’enregistrer la cause : l’exception est absente."
        )
        return redirect(redirect_url)

    if not commentaire:
        messages.warning(
            request,
            "Veuillez saisir un commentaire."
        )
        return redirect(redirect_url)

    allowed_types = {
        "Application",
        "Configuration",
        "Script",
        "Environment",
    }

    if cause_type not in allowed_types:
        messages.error(
            request,
            "Le type de cause sélectionné n’est pas valide."
        )
        return redirect(redirect_url)

    if not test_case_id or not test_step_id:
        messages.error(
            request,
            "Impossible d’enregistrer la cause : "
            "le test ou l’étape n’est pas identifié."
        )
        return redirect(redirect_url)

    test_case = TestCase.objects.filter(
        id=test_case_id
    ).first()

    test_step = TestStep.objects.filter(
        id=test_step_id
    ).first()

    if test_case is None:
        messages.error(
            request,
            "Impossible d’enregistrer la cause : "
            "le test demandé n’existe pas."
        )
        return redirect(redirect_url)

    if test_step is None:
        messages.error(
            request,
            "Impossible d’enregistrer la cause : "
            "l’étape demandée n’existe pas."
        )
        return redirect(redirect_url)

    try:
        with transaction.atomic():

            existing = ErrorCauseFromUser.objects.filter(
                exception=exception,
                testCase=test_case,
                testStep=test_step
            ).order_by("-id").first()

            if existing is None:

                entry = ErrorCauseFromUser.objects.create(
                    testCase=test_case,
                    testStep=test_step,
                    exception=exception,
                    action=action,
                    errorMessage=error_message,
                    commentaire=commentaire,
                    type=cause_type
                )

                messages.success(
                    request,
                    "La nouvelle cause a été enregistrée."
                )

                logger.info(
                    "Cause créée : id=%s, type=%s, "
                    "testCase=%s, testStep=%s",
                    entry.id,
                    cause_type,
                    test_case.id,
                    test_step.id
                )

            else:
                changed_fields = []

                # Vérification du commentaire
                if existing.commentaire != commentaire:
                    existing.commentaire = commentaire
                    changed_fields.append("commentaire")

                # Vérification du type
                if existing.type != cause_type:
                    existing.type = cause_type
                    changed_fields.append("type")

                # Vérification du message technique
                if existing.errorMessage != error_message:
                    existing.errorMessage = error_message
                    changed_fields.append("errorMessage")

                # Vérification du nom de l’action
                if existing.action != action:
                    existing.action = action
                    changed_fields.append("action")

                if changed_fields:
                    existing.save(
                        update_fields=changed_fields
                    )

                    messages.success(
                        request,
                        "La cause existante a été mise à jour. "
                        "Champs modifiés : "
                        + ", ".join(changed_fields)
                        + "."
                    )

                    logger.info(
                        "Cause mise à jour : id=%s, "
                        "champs=%s, type=%s",
                        existing.id,
                        changed_fields,
                        cause_type
                    )

                else:
                    messages.info(
                        request,
                        "Cette cause est déjà enregistrée. "
                        "Aucune modification n’a été détectée."
                    )

    except DatabaseError:
        logger.exception(
            "Erreur de base de données pendant l’enregistrement : "
            "exception=%s, testCase=%s, testStep=%s",
            exception,
            test_case_id,
            test_step_id
        )

        messages.error(
            request,
            "Une erreur de base de données empêche "
            "l’enregistrement de la cause."
        )

    except Exception:
        logger.exception(
            "Erreur inattendue pendant l’enregistrement : "
            "exception=%s, testCase=%s, testStep=%s",
            exception,
            test_case_id,
            test_step_id
        )

        messages.error(
            request,
            "Une erreur inattendue s’est produite "
            "pendant l’enregistrement."
        )

    return redirect(redirect_url)