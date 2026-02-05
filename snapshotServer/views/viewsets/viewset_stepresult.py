import json
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.controllers.error_cause_finder import ErrorCauseFinder
from snapshotServer.models import StepResult, TestCaseInSession, Error, TestStep
from snapshotServer.viewsets import ResultRecordingViewSet

logger = logging.getLogger(__name__)

class StepResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepResult
        fields = ('id', 'step', 'testCase', 'result', 'duration', 'stacktrace')

class StepResultPermission(ApplicationSpecificPermissionsResultRecording):

    def get_object_application(self, step_result):
        if step_result:
            return step_result.testCase.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        if request.POST.get('testCase', ''): # POST
            return TestCaseInSession.objects.get(pk=request.data['testCase']).session.version.application
        elif view.kwargs.get('pk', ''): # PATCH needed so that we can refuse access if object is unknown
            return self.get_object_application(StepResult.objects.get(pk=view.kwargs['pk']))
        else:
            return ''

class StepResultViewSet(ResultRecordingViewSet): # post / patch
    http_method_names = ['post', 'patch']
    queryset = StepResult.objects.all()
    serializer_class = StepResultSerializer
    permission_classes = [StepResultPermission]

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self.parse_stacktrace(serializer)
        self.analyze_test_run(serializer)


    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.parse_stacktrace(serializer)
        self.analyze_test_run(serializer)

    def analyze_test_run(self, serializer):
        """
        Analyze step run when we get the 'Test end' step and stacktrace is complete, if test case is KO
        :param serializer:
        :return:
        """
        if (serializer.instance.step.name == TestStep.LAST_STEP_NAME
            and serializer.instance.stacktrace
            and len(serializer.instance.stacktrace) > 100
            and serializer.instance.testCase
            and not serializer.instance.testCase.isOkWithResult()):
            error_cause_finder = ErrorCauseFinder(serializer.instance.testCase)
            error_cause = error_cause_finder.detect_cause()
            if error_cause:
                failed_step_result = StepResult.objects.filter(testCase=serializer.instance.testCase, result=False).exclude(step__name=TestStep.LAST_STEP_NAME).order_by('-pk')
                errors = Error.objects.filter(stepResult = failed_step_result)
                if len(errors):
                    error = errors[0]
                    error.cause = error_cause.cause
                    error.causedBy = error_cause.why
                    error.causeDetails = error_cause.information
                    error.causeAnalysisErrors = '\n'.join(error_cause.analysis_errors)
                    error.save()


    def parse_stacktrace(self, serializer):
        """
        parse the stacktrace, looking for action in error
        """
        if not serializer.data['result']:
            try:
                step_result_details = json.loads(serializer.validated_data['stacktrace'])
                if step_result_details['name'] == TestStep.LAST_STEP_NAME:
                    return

                failed_action, exception, exception_message = self.search_failed_action(step_result_details, step_result_details['action'])

                failed_action = failed_action if failed_action else step_result_details['name']
                exception = exception if exception else step_result_details['exception']
                exception_message = exception_message if exception_message else step_result_details['exceptionMessage']

                # delete errors linked to this StepResult, in case a new stacktrace is submitted
                Error.objects.filter(stepResult=serializer.instance).delete()

                error = Error(stepResult = serializer.instance,
                              action = failed_action,
                              exception = exception,
                              errorMessage = exception_message,
                              )
                error.save()
                related_errors = self.search_related_errors(error)

                if len(related_errors):
                    error.relatedErrors.set(related_errors)

            except Exception as e:
                logger.error("Error parsing stacktrace: " + str(e))

    def search_related_errors(self, error):
        """
        Search for similar errors in a time frame of 1 hour

        """
        return Error.objects.filter(
            action = error.action,
            exception = error.exception,
            errorMessage = error.errorMessage,
            stepResult__testCase__date__gte=timezone.now() - timedelta(seconds=3600)
        ).exclude(pk=error.id)

    def search_failed_action(self, data, path=''):
        """
        Look for an action that has the 'failed' flag set to true and return the name and the exception message, if it's present
        """

        if 'actions' in data:

            for action in data['actions']:

                if action.get('type') == 'step' and 'actions' in action:
                    failed_action, exception, exception_message = self.search_failed_action(action, path + '>' + action['action'])
                    if failed_action:
                        return failed_action, exception, exception_message

                if action.get('failed', False):
                    if action.get('element', ''):
                        return f"{path}>{action['action']} on {action['origin']}.{action['element']}", action.get('exception', None), action.get('exceptionMessage', None)
                    else:
                        return f"{path}>{action['action']} in {action['origin']}", action.get('exception', None), action.get('exceptionMessage', None)

        return None, None, None