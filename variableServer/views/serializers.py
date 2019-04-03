'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers

from variableServer.models import Variable, TestCase
        
class VariableSerializer(serializers.ModelSerializer):
    
    test = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=TestCase.objects.all())
    
    class Meta:
        model = Variable
        fields = ('id', 'name', 'value', 'environment', 'version', 'test', 'releaseDate', 'internal', 'protected', 'description', 'application', 'reservable', 'timeToLive', 'creationDate')

    def create(self, validated_data):
        """
        Override the create method, so that we can correct reservable state.
        This method is already called inside save() method, but at this stage, using REST API, test list has not already been set
        Do this later so that tests are initialized
        """
        instance = super(VariableSerializer, self).create(validated_data)
        instance._correctReservableState()
        return instance
        