from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token
from django.db.models import Q
import snapshotServer
import django.test
from snapshotServer.controllers.DiffComputer import DiffComputer
import logging

def _create_allowed_user_and_group():
    
    try:
        user = User.objects.get(username='user')
    except User.DoesNotExist as e:
        user = User.objects.create_user(username='user', password='pwd')
    group, created = Group.objects.get_or_create(name='Snapshot Users')
    ct = ContentType.objects.get_for_model(snapshotServer.models.ExcludeZone)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_excludezone') | Q(codename='change_excludezone') | Q(codename='delete_excludezone') , content_type=ct))
    ct = ContentType.objects.get_for_model(snapshotServer.models.Snapshot)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_snapshot') | Q(codename='change_snapshot') | Q(codename='delete_snapshot') , content_type=ct))
    
    ct = ContentType.objects.get_for_model(snapshotServer.models.TestCaseInSession)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_testcaseinsession') | Q(codename='change_testcaseinsession') , content_type=ct))
    ct = ContentType.objects.get_for_model(snapshotServer.models.Application)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_application') | Q(codename='change_application') , content_type=ct))
    
    group.user_set.add(user)
    
    return user

def authenticate_test_client_for_api(client):
    """
    from client of django rest_framework, creates a user / group and add HTTP_AUTHORIZATION header to request
    @param client: DRF client
    """
    user = _create_allowed_user_and_group()
    
    token = Token.objects.get_or_create(user=user)[0]
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

def authenticate_test_client_for_web_view(client):
    """
    from client of django web views, creates a user / group and login
    @param client: django client
    """
    user = _create_allowed_user_and_group()
    client.login(username='user', password='pwd')
    
    
class SnapshotTestCase(django.test.TestCase):
    
    def tearDown(self):
        DiffComputer.stopThread()
        logging.error("Stop threads")
        super().tearDown()