from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token
from django.db.models import Q
import snapshotServer
import variableServer

def authenticate_test_client(client):
    """
    from client of django rest_framework, creates a user / group
    """
    try:
        user = User.objects.get(username='user')
    except User.DoesNotExist as e:
        user = User.objects.create_user(username='user', password='pwd')
    group, created = Group.objects.get_or_create(name='Variable Users')

    ct = ContentType.objects.get_for_model(variableServer.models.Application)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_application') | Q(codename='change_application') , content_type=ct))
    ct = ContentType.objects.get_for_model(variableServer.models.Variable)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable') | Q(codename='delete_variable') , content_type=ct))
    
    group.user_set.add(user)
    
    token = Token.objects.get_or_create(user=user)[0]
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
def authenticate_test_client_with_see_protected_vars(client):
    """
    from client of django rest_framework, creates a user / group
    """
    try:
        user = User.objects.get(username='user')
    except User.DoesNotExist as e:
        user = User.objects.create_user(username='user', password='pwd')
    group, created = Group.objects.get_or_create(name='Variable Users')

    ct = ContentType.objects.get_for_model(variableServer.models.Application)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_application') | Q(codename='change_application') , content_type=ct))
    ct = ContentType.objects.get_for_model(variableServer.models.Variable)
    group.permissions.add(*Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable') | Q(codename='see_protected_var') , content_type=ct))
    
    group.user_set.add(user)
    
    token = Token.objects.get_or_create(user=user)[0]
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)