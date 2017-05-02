'''
Created on 8 mars 2017

@author: worm
'''
import os

def getTestDirectory():
    return os.path.dirname(os.path.dirname(__file__)) + os.sep +  'tests' + os.sep + 'data' + os.sep