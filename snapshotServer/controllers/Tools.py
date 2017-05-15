'''
Created on 15 mai 2017

@author: bhecquet
'''
import traceback

def isTestMode():
    """
    Returns true if we detect the TestCase class in stack
    """
    
    for line in traceback.extract_stack(None):
        if 'unittest' in line.filename:
            return True

    return False
