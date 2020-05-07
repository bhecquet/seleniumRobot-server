This file reference list of functional tests that should be executed before releasing

# Variable server #

## From seleniumRobot ##

- get list of variables
- reserve a variable
- create a custom variable from test, with a short TTL
- get this custom variable
- check automatic dereservation of the variable after 15 mins

## From admin interface ##

- Copy variable
- Delete variable
- Modify variable
- Check Time to live

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