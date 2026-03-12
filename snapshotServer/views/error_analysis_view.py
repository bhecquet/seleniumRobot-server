'''
Created on 11 mars 2026

@author: S047432
'''
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView

from snapshotServer.controllers.error_cause.error_cause_finder import ErrorCauseFinderExecutor
from snapshotServer.models import TestCaseInSession
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultConsultation

logger = logging.getLogger(__name__)


class ErrorAnalysisPermission(ApplicationSpecificPermissionsResultConsultation):

    def get_object_application(self, test_case_in_session):
        if test_case_in_session:
            return test_case_in_session.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        test_case_in_session_id = view.kwargs.get('test_case_in_session_id', '')
        if test_case_in_session_id:
            try:
                return self.get_object_application(TestCaseInSession.objects.get(pk=test_case_in_session_id))
            except TestCaseInSession.DoesNotExist:
                return ''
        return ''


class ErrorAnalysisView(CreateAPIView):
    """
    API view to re-trigger an error cause analysis for a given TestCaseInSession.
    Called from the web interface (IHM).

    POST /snapshot/errorAnalysis/<test_case_in_session_id>/
        URL parameter: test_case_in_session_id (int) - pk of the TestCaseInSession to analyse
    """

    queryset = TestCaseInSession.objects.none()
    permission_classes = [ErrorAnalysisPermission]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        test_case_in_session = get_object_or_404(TestCaseInSession, pk=kwargs['test_case_in_session_id'])
        ErrorCauseFinderExecutor.submit(test_case_in_session)

        return HttpResponse(status=200)

