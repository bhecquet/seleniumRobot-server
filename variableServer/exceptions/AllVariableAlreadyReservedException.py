'''
Created on 8 déc. 2017

@author: S047432
'''
from rest_framework.exceptions import APIException

class AllVariableAlreadyReservedException(APIException):
    status_code = 423
    default_detail = 'All variables are already reserved/locked'
    default_code = 'locked'
