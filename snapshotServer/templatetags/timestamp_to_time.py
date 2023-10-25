"""
from https://stackoverflow.com/questions/9056016/how-do-i-convert-unix-timestamp-in-integer-to-human-readable-format-in-django-te
"""

from django import template    
import datetime
register = template.Library()    

@register.filter('timestamp_to_time')
def convert_timestamp_to_time(timestamp):
    if timestamp:
        return datetime.datetime.utcfromtimestamp(int(timestamp) / 1000.0).strftime('%H:%M:%S') + f".{timestamp % 1000}"
    else:
        return ''