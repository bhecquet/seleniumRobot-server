import datetime

from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.response import Response

from commonsServer import preferences
from seleniumRobotServer.permissions.permissions import GenericPermissions


class InactiveUsersPermissions(GenericPermissions):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and (request.user.has_perm('auth.view_user') or request.user.is_superuser))

class InactiveUsers(APIView):

    # allow anyone on this view
    queryset = User.objects.none()
    permission_classes = [InactiveUsersPermissions]

    def get(self, request, *args, **kwargs):
        max_inactive_days = preferences.get_preference("USER_MAX_INACTIVE_DAYS")

        inactive_users = User.objects.filter(last_login__lt=timezone.now() - datetime.timedelta(days=int(max_inactive_days)))

        return Response([{"username": user.username,
                 "lastLogin": user.last_login,
                 "firstName": user.first_name,
                 "lastName": user.last_name} for user in inactive_users])
