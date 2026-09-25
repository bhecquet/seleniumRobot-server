'''
Created on 25 janv. 2017

@author: worm
'''

from django.conf import settings
from rest_framework import serializers

from variableServer.models import Variable, TestCase


def _prevent_value_and_uploadfile_setting(validated_data):
    """
    Prevent setting a file and a value at the same time
    File will have priority
    :param validated_data:
    """

    if validated_data.get('uploadFile', None):
        validated_data['value'] = ''
    elif validated_data.get('value', None):
        validated_data['uploadFile'] = None


class VariableSerializer(serializers.ModelSerializer):
    
    test = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=TestCase.objects.all())
    
    class Meta:
        model = Variable
        fields = ('id', 'name', 'value', 'uploadFile', 'environment', 'version', 'test', 'releaseDate', 'internal', 'protected', 'description', 'application', 'reservable', 'timeToLive', 'creationDate')

    def create(self, validated_data):
        """
        Override the create method, so that we can correct reservable state.
        This method is already called inside save() method, but at this stage, using REST API, test list has not already been set
        Do this later so that tests are initialized
        """
        _prevent_value_and_uploadfile_setting(validated_data)
        instance = super(VariableSerializer, self).create(validated_data)
        instance._correctReservableState()
        return instance

    def update(self, instance, validated_data):

        _prevent_value_and_uploadfile_setting(validated_data)
        return super().update(instance, validated_data)

