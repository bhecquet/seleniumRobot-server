import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from commonsServer.models import AppPreference
from commonsServer.preferences import sync_defaults
from variableServer.models import Application, TestEnvironment

logger = logging.getLogger(__name__)

class CustomUserAdmin(UserAdmin):
    """
    When variables edition permission is provided, also provide permission to view results for the same application
    """

    def save_related(self, request, form, formsets, change):

        super().save_related(request, form, formsets, change)

        user = form.instance

        application_content_type = ContentType.objects.get_for_model(Application, False)
        environment_content_type = ContentType.objects.get_for_model(TestEnvironment, False)

        all_permissions = user.user_permissions.all()
        for permission in all_permissions:
            if permission.codename.startswith(Application.app_variable_permission_code):
                app = permission.codename.replace(Application.app_variable_permission_code, '')

                try:
                    permission = Permission.objects.get(
                        codename=Application.app_result_permission_code + app,
                        content_type=application_content_type,
                    )
                    user.user_permissions.add(permission)
                except:
                    logger.error(f"view result permission not created for '{app}'")

            elif permission.codename.startswith(TestEnvironment.env_variable_permission_code):
                env = permission.codename.replace(TestEnvironment.env_variable_permission_code, '')

                try:
                    permission = Permission.objects.get(
                        codename=TestEnvironment.env_result_permission_code + env,
                        content_type=environment_content_type,
                    )
                    user.user_permissions.add(permission)
                except:
                    logger.error(f"view result permission not created for '{env}'")

class AppPreferenceAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "value", "description")
    fields = ("key", "value", "initialValue", "description")
    readonly_fields = ("initialValue",)
    ordering = ("key",)

    def get_queryset(self, request):
        sync_defaults()
        return super().get_queryset(request)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(AppPreference, AppPreferenceAdmin)