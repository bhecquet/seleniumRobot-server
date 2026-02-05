'''
Created on 25 janv. 2017

@author: worm
'''

from django.conf import settings
from rest_framework import serializers

from variableServer.admin_site.base_model_admin import is_user_authorized
from variableServer.models import Variable, TestCase


class VariableSerializer(serializers.ModelSerializer):
    
    test = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=TestCase.objects.all())
    
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.security_api_enabled = bool(getattr(settings, 'SECURITY_API_ENABLED', True))
    
    class Meta:
        model = Variable
        fields = ('id', 'name', 'value', 'uploadFile', 'environment', 'version', 'test', 'releaseDate', 'internal', 'protected', 'description', 'application', 'reservable', 'timeToLive', 'creationDate')

    def create(self, validated_data):
        """
        Override the create method, so that we can correct reservable state.
        This method is already called inside save() method, but at this stage, using REST API, test list has not already been set
        Do this later so that tests are initialized
        """
        instance = super(VariableSerializer, self).create(validated_data)
        instance._correctReservableState()
        return instance
        
    def to_representation(self, instance):
        """
        Mask value if user has not permission to see it
        """
        ret = super().to_representation(instance)
        
        if (self.security_api_enabled and not is_user_authorized(self.context['request'].user)):
            ret['value'] = instance.valueProtected()
        return ret