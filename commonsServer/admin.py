from rest_framework.authtoken.admin import TokenAdmin
from django.contrib import admin

TokenAdmin.raw_id_fields = ['user']

@admin.display(description="Token")
def mask_token(obj):
    return obj.key[0: 2] + "****" + obj.key[-3:]

TokenAdmin.list_display = ('user', 'created', mask_token)