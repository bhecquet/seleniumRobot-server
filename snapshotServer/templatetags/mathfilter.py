"""
Code get from https://github.com/dbrgn/django-mathfilters
Copyright (c) 2012--2020 Danilo Bargen and contributors

"""

from django.template import Library
from decimal import Decimal

register = Library()

@register.filter
def div(value, arg):
    """Divide the arg by the value."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '/'
        )
        return nvalue / narg
    except (ValueError, TypeError):
        try:
            return value / arg
        except Exception:
            return ''
        

def handle_float_decimal_combinations(value, arg, operation):
    if isinstance(value, float) and isinstance(arg, Decimal):
        value = Decimal(str(value))
    if isinstance(value, Decimal) and isinstance(arg, float):
        arg = Decimal(str(arg))
    return value, arg


def valid_numeric(arg):
    if isinstance(arg, (int, float, Decimal)):
        return arg
    try:
        return int(arg)
    except ValueError:
        return float(arg)
