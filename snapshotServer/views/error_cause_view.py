import logging

from django.db import transaction
from django.http import JsonResponse
from django.views import View

from snapshotServer.forms import ErrorCauseForm
from snapshotServer.models import ErrorCauseFromUser


logger = logging.getLogger(__name__)


class SaveErrorCauseView(View):

    def post(self, request, *args, **kwargs):
        form = ErrorCauseForm(request.POST)

        if not form.is_valid():
            return JsonResponse(
                {
                    "success": False,
                    "message": "Les données envoyées ne sont pas valides.",
                    "errors": form.errors.get_json_data(),
                },
                status=400,
            )

        exception = form.cleaned_data["exception"].strip()
        error_message = form.cleaned_data["errorMessage"].strip()
        action = form.cleaned_data["stepName"].strip()
        comment = form.cleaned_data["comment"].strip()
        cause_type = form.cleaned_data["cause"]

        test_case = form.cleaned_data["testCaseId"]
        test_step = form.cleaned_data["testStepId"]

        try:
            with transaction.atomic():
                existing = (
                    ErrorCauseFromUser.objects
                    .filter(
                        exception=exception,
                        testCase=test_case,
                        testStep=test_step,
                    )
                    .order_by("-id")
                    .first()
                )

                if existing is None:
                    ErrorCauseFromUser.objects.create(
                        testCase=test_case,
                        testStep=test_step,
                        exception=exception,
                        action=action,
                        errorMessage=error_message,
                        comment=comment,
                        type=cause_type,
                    )

                    return JsonResponse(
                        {
                            "success": True,
                            "message": (
                                "La nouvelle cause a été enregistrée."
                            ),
                        },
                        status=201,
                    )

                existing.comment = comment
                existing.type = cause_type
                existing.errorMessage = error_message
                existing.action = action
                existing.save()

                return JsonResponse(
                    {
                        "success": True,
                        "message": (
                            "La cause existante a été mise à jour."
                        ),
                    },
                    status=200,
                )

        except Exception:
            logger.exception(
                "Erreur pendant l’enregistrement de la cause : "
                "exception=%s, testCase=%s, testStep=%s",
                exception,
                test_case.id,
                test_step.id,
            )

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Une erreur s’est produite pendant "
                        "l’enregistrement de la cause."
                    ),
                },
                status=500,
            )