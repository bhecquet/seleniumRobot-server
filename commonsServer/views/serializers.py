'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from commonsServer.models import Application, TestEnvironment, Version, TestCase

class NoUniqueValidationMixin:
    """
    Delete UniqueValidator/UniqueTogetherValidator auto-added by DRF
    Uniqueness is checked in viewsets
    """
    def get_validators(self):
        return [
            v for v in super().get_validators()
            if not isinstance(v, (UniqueValidator, UniqueTogetherValidator))
        ]

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(field_name, model_field)

        # delete validator on field
        field_kwargs.pop('validators', None)
        return field_class, field_kwargs

class ApplicationSerializer(NoUniqueValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'name',)

class VersionSerializer(NoUniqueValidationMixin, serializers.ModelSerializer):
    
    class Meta:
        model = Version
        fields = ('id', 'name', 'application')


class TestEnvironmentSerializer(NoUniqueValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = TestEnvironment
        fields = ('id', 'name',)

class TestCaseSerializer(NoUniqueValidationMixin, serializers.ModelSerializer):

    class Meta:
        model = TestCase
        fields = ('id', 'name', 'application')
        