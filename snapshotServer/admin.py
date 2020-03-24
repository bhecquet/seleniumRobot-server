from django.contrib import admin
from snapshotServer.models import TestSession

# Register your models here.

class TestSessionAdmin(admin.ModelAdmin): 
    list_display = ('sessionId', 'name', 'date', 'environment', 'ttl')
    list_filter = ('version__application',)
    search_fields = ['name']
    actions = ['delete_selected']

admin.site.register(TestSession, TestSessionAdmin)
