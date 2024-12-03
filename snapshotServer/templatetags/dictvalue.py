'''
Created on 3 déc. 2024

@author: S047432
'''
from django.template import Library
register = Library()

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)
