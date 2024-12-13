from django.contrib import admin
from variableServer.models import Variable, TestCase, Application, Version
from variableServer.models import TestEnvironment

from variableServer.admin_site.application_admin import ApplicationAdmin
from variableServer.admin_site.test_case_admin import TestCaseAdmin
from variableServer.admin_site.version_admin import VersionAdmin
from variableServer.admin_site.variable_admin import VariableAdmin
from variableServer.admin_site.environment_admin import EnvironmentAdmin



# Register your models here.
admin.site.disable_action('delete_selected')
admin.site.register(Application, ApplicationAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(TestEnvironment, EnvironmentAdmin)