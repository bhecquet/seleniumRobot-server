'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers

from elementInfoServer.models import ElementInfo

class ElementInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementInfo
        fields = ('id', 'application', 'version', 'uuid', 'name', 'locator', 'tagName', 'text', 'width', 'height', 'coordX', 'coordY', 'lastUpdate', 'b64Image', 'attributes', 'totalSearch', 'tagStability', 'textStability', 'rectangleStability', 'b64ImageStability', 'attributesStability')
