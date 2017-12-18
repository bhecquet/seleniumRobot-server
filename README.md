# seleniumRobot-server #
Server that supports seleniumRobot executions
Features:
- serves variables for seleniumRobot tests
- store test results if requested
- store and compare snapshots if requested

# Build #
For now, build is done through the python script `build.py`. Ite generates a zip file which you only need to unzip

# Installation #
- python install
- apache install
    - apache from apachelounge, same bitness as python
    - C++ redistributable microsoft, same version as the one used for apache compilation
    - mod_wsgi, same bitness as python
- deploy files: unzip seleniumRobotServer.zip
- install python requirements: `pip install -r requirements.txt` 
- database migration: `python manage.py migrate`
- database fix: `python manage.py fix_permissions`
- create super user on first deploy **ONLY**: `python manage.py createsuperuser`

# Usage #

## User interface ##
TBC

## API ##

### variables ###

To get variables from server: `http://<server>:<port>/variable/api/variable?version=7&environment=1&test=8&format=json`
Ids can be found through user interface. 
`format=json` is mandatory so that getting variable list is not done twice, thus reserving variables twice

