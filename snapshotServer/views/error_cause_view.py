import re
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from snapshotServer.models import ErrorCauseFromUser, TestStep, TestCase
from django.contrib import messages


@csrf_exempt
def save_error_cause(request):

    if request.method == "POST":

        exception = request.POST.get("exception")
        raw_message = request.POST.get("errorMessage")
        action = request.POST.get("stepName")
        commentaire = request.POST.get("commentaire")
        cause_type = request.POST.get("cause")

        error_message = raw_message

        test_step_id = request.POST.get("testStepId")
        test_step = TestStep.objects.filter(id=test_step_id).first()


        test_case_id = request.POST.get("testCaseId")
        test_case = TestCase.objects.filter(id=test_case_id).first()

        existing = ErrorCauseFromUser.objects.filter(
            exception=exception,
            testCase=test_case,
            testStep=test_step
        ).first()


        if existing:


            if existing.commentaire != commentaire:
                existing.commentaire = commentaire
                existing.errorMessage = error_message
                existing.type = cause_type
                existing.save()

                messages.success(request, "Cause mise à jour ")

            else:
                messages.info(request, "Cette cause est déjà enregistrée")


        else:
            ErrorCauseFromUser.objects.create(
                testCase=test_case,
                testStep=test_step,
                exception=exception,
                action=action,
                errorMessage=error_message,
                commentaire=commentaire,
                type=cause_type
            )

            messages.success(request, "Cause enregistrée ")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')