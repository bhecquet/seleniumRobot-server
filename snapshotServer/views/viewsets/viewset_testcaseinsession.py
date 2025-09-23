from rest_framework import serializers

from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import TestCaseInSession, TestSession, TestStepsThroughTestCaseInSession, TestStep
from snapshotServer.viewsets import ResultRecordingViewSet


class TestCaseInSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCaseInSession
        fields = ('id', 'session', 'testCase', 'testSteps', 'stacktrace', 'isOkWithSnapshots', 'computed', 'name', 'computingError', 'status', 'gridNode', 'description', 'date')

    def create(self, validated_data):

        # do not create if it exists
        tcss = TestCaseInSession.objects.filter(**validated_data)
        if len(tcss) > 0:
            test_case_in_sesssion = tcss[0]
        else:
            test_case_in_sesssion = super(TestCaseInSessionSerializer, self).create(validated_data)

        # add test steps
        self._update_test_steps(test_case_in_sesssion)

        return test_case_in_sesssion

    def _update_test_steps(self, test_case_in_sesssion):
        if 'testSteps' in self.initial_data:

            for step_through_test_case_in_session in TestStepsThroughTestCaseInSession.objects.filter(testcaseinsession=test_case_in_sesssion):
                step_through_test_case_in_session.delete(keep_parents=True)

            for i, step_id in enumerate(self.initial_data.getlist('testSteps', [])):
                step_through_test_case_in_session = TestStepsThroughTestCaseInSession(order=i, teststep=TestStep.objects.get(pk=int(step_id)), testcaseinsession=test_case_in_sesssion)
                step_through_test_case_in_session.save()


    def update(self, instance, validated_data):

        self._update_test_steps(instance)

        return super(TestCaseInSessionSerializer, self).update(instance, validated_data)



class TestCaseInSessionPermission(ApplicationSpecificPermissionsResultRecording):
    """
    Redefine permission class so that it's possible to get application from data
    """

    def get_object_application(self, test_case_in_session):
        if test_case_in_session:
            return test_case_in_session.session.version.application
        else:
            return ''

    def get_application(self, request, view):
        if request.POST.get('session', ''): # POST
            return TestSession.objects.get(pk=request.data['session']).version.application
        elif view.kwargs.get('pk', ''): # PATCH / GET, needed so that we can refuse access if object is unknown
            return self.get_object_application(TestCaseInSession.objects.get(pk=view.kwargs['pk']))
        else:
            return ''

class TestCaseInSessionViewSet(ResultRecordingViewSet): # post / get / patch
    http_method_names = ['post', 'get', 'patch']
    queryset = TestCaseInSession.objects.all()
    serializer_class = TestCaseInSessionSerializer
    permission_classes = [TestCaseInSessionPermission]
