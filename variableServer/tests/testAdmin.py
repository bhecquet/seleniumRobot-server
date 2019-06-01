'''
Created on 28 mars 2018

@author: s047432
'''

# tests we should add to check admin view behavior
# - when permissions are set for application, 
#   - cannot delete Variable of application whose user does not have right for
#   - cannot delete TestCase of application whose user does not have right for
#   - cannot delete Version of application whose user does not have right for
#   - variable belonging to restricted application are not shown
#   - test case belonging to restricted application are not shown
#   - version belonging to restricted application are not shown
#   - cannot change several variable at once to/from restricted application
#   - cannot copy several variable to/from restricted application
#   - cannot add variable to a restricted application
#   - cannot add testcase to a restricted application
#   - cannot add version to a restricted application
#   - for unrestricted applications, check the above behavior are not active
# - change multiple variables at once
# - copy multiple variables
# - copy several variables, one with tests, other without and check that resulting test is none
# - copy several variables, all with tests and check that resulting tests are the same as from variables