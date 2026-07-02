from django.contrib import admin

from snapshotServer.models import TestSession, StepReference

from snapshotServer.admin_site.stepreference_admin import StepReferenceAdmin
from snapshotServer.admin_site.testsession_admin import TestSessionAdmin


admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(StepReference, StepReferenceAdmin)
