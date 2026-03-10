import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from variableServer.models import Application

logger = logging.getLogger(__name__)

class CustomUserAdmin(UserAdmin):
    """
    When variables edition permission is provided, also provide permission to view results for the same application
    """

    def save_related(self, request, form, formsets, change):

        super().save_related(request, form, formsets, change)

        user = form.instance

        content_type = ContentType.objects.get_for_model(Application, False)

        all_permissions = user.user_permissions.all()
        for permission in all_permissions:
            if permission.codename.startswith(Application.app_variable_permission_code):
                app = permission.codename.replace(Application.app_variable_permission_code, '')

                try:
                    permission = Permission.objects.get(
                        codename=Application.app_result_permission_code + app,
                        content_type=content_type,
                    )
                    user.user_permissions.add(permission)
                except:
                    logger.error(f"view result permission not created for '{app}'")

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)