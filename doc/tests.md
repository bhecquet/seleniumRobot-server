This file reference list of functional tests that should be executed before releasing

# Variable server #

## From seleniumRobot ##

- get list of variables
- reserve a variable
- create a custom variable from test, with a short TTL
- get this custom variable
- check automatic dereservation of the variable after 15 mins

### permissions ###

- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN disabled: all variable server objects are available according to permission affected on user
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change version of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change testcase of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change variable of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: cannot create / change / modify application with applicaton specific rights
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: cannot create / change / modify environment with applicaton specific rights
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: django permission on testcase, version, variable are complementary to application specific permission

## From admin interface ##

- Copy variable
- Delete variable
- Modify variable
- Check Time to live

### permissions ###

- password requested to connect to admin
- staff flag must be set to access administration (django feature)
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN disabled: object administration depends on rights affected to users
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change version of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change testcase of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: can view / create / delete / change variable of an application we have right for
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: cannot create / change / modify application with applicaton specific rights
- RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN enabled: cannot create / change / modify environment with applicaton specific rights

# Snapshot server #

## From seleniumRobot ##

- Send snapshot from a test
- Have a snapshot with custom exclusion zones and check they are present in interface and associated to this test session only, not the reference snapshot
- Check seleniumRobot report displays the snapshot comparison tab and this one is usable (exclusion zones are editable)

## From GUI ##

- Check display of session list
- Select a test session and review displayed differences
- Add / remove exclude zone that applies to reference image and see if all test sessions are impacted
- Add / remove an exclude zone that applies to the session snapshot and check it only applies to it.