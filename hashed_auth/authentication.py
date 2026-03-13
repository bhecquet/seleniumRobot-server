import hashlib

import rest_framework.authentication
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import PBKDF2PasswordHasher

def crypt_token(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()

class TokenAuthentication(rest_framework.authentication.TokenAuthentication):
    """
    Simple token based authentication, inherited from DRF TokenAuthentication

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'Token'
    model = None

    def get_model(self):
        if self.model is not None:
            return self.model
        from hashed_auth.models import Token
        return Token

    """
    A custom token model may be used, but must have the following properties.

    * key -- The string identifying the token
    * user -- The user to which the token belongs
    """

    def authenticate_credentials(self, key):

        model = self.get_model()

        try:
            token = model.objects.get(key=crypt_token(key))
        except:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (token.user, token)



    def verify(self, raw, token):
        return check_password(raw, token.key)

