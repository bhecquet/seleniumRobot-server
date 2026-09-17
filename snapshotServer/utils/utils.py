'''
Created on 8 mars 2017

@author: worm
'''
import os

def get_test_directory():
    return os.path.dirname(os.path.dirname(__file__)) + os.sep +  'tests' + os.sep + 'data' + os.sep