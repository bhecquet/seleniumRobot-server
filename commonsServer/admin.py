import logging

from django.contrib import admin
from django.contrib.auth import get_backends
from django.contrib.auth.admin import UserAdmin, GroupAdmin as GroupAdminDefault
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType

from django.utils.html import format_html_join

from commonsServer.forms import GroupAdminForm
from commonsServer.models import AppPreference
from commonsServer.preferences import sync_defaults
from snapshotServer.models import TestSession
from variableServer.models import Application, TestEnvironment

try:
    from django_auth_ldap.backend import LDAPBackend, _LDAPUser
except ImportError:
    LDAPBackend = None
    _LDAPUser = None

logger = logging.getLogger(__name__)

class CustomUserAdmin(UserAdmin):
    """
    When variables edition permission is provided, also provide permission to view results for the same application
    """

    readonly_fields = ('effective_permissions',)

    def get_fieldsets(self, request, obj=None):
        fs = UserAdmin.fieldsets
        if 'effective_permissions' not in fs[2][1]['fields']:
            fs[2][1]['fields'] = fs[2][1]['fields'] + ('effective_permissions',)
        return fs

    @admin.display(description='Effective permissions')
    def effective_permissions(self, obj):
        if not obj or not obj.pk:
            return ''

        permissions = set(obj.get_all_permissions())
        permissions |= self._get_ldap_group_permissions(obj)

        return format_html_join('', '{}<br>', ((p,) for p in sorted(permissions)))

    @staticmethod
    def _get_ldap_group_permissions(user):
        """
        Permissions granted through LDAP group membership are only computed and
        cached by django-auth-ldap when the user actually logs in (they are
        stored on the transient 'user.ldap_user' attribute of the in-memory
        User instance). As the admin displays permissions for a User fetched
        fresh from the database, this information is missing.
        To get it anyway, query each configured LDAP backend directly: this
        uses the backend's service account (AUTH_LDAP_x_BIND_DN /
        AUTH_LDAP_x_BIND_PASSWORD) to look up the user's LDAP groups and
        resolve the corresponding Django permissions, without requiring the
        user to authenticate.
        """
        permissions = set()

        if LDAPBackend is None:
            return permissions

        for backend in get_backends():
            if not isinstance(backend, LDAPBackend):
                continue

            try:
                ldap_user = _LDAPUser(backend, username=user.username)
                permissions |= ldap_user.get_group_permissions()
            except Exception:
                logger.warning("could not retrieve LDAP group permissions for user '%s'", user.username, exc_info=True)

        return permissions

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


        self.add_view_test_session_permission(user)

    @staticmethod
    def add_view_test_session_permission(user):
        testsession_content_type = ContentType.objects.get_for_model(TestSession, True)
        has_permission_on_application_or_environment = False

        for permission in user.user_permissions.all():
            if permission.codename.startswith(Application.app_result_permission_code) or permission.codename.startswith(TestEnvironment.env_result_permission_code):
                has_permission_on_application_or_environment = True

        # add the 'view session' permission if user can see at least some results
        if has_permission_on_application_or_environment:
            permission = Permission.objects.get(
                codename='view_testsession',
                content_type=testsession_content_type,
            )
            user.user_permissions.add(permission)

# from https://github.com/Microdisseny/django-groupadmin-users
class GroupAdmin(GroupAdminDefault):

    form = GroupAdminForm
    filter_horizontal = ['permissions']

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
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
admin.site.register(AppPreference, AppPreferenceAdmin)