import secrets

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

from hashed_auth.authentication import MyPBKDF2PasswordHasher


class Token(models.Model):
    """
    The default authorization token model.
    """
    raw_key = ""
    key = models.CharField(_("Key"), max_length=128)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='hashed_auth_token',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        # Work around for a bug in Django:
        # https://code.djangoproject.com/ticket/19422
        #
        # Also see corresponding ticket:
        # https://github.com/encode/django-rest-framework/issues/705
        abstract = 'hashed_auth.apps.AuthTokenConfig' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        """
        Save the token instance.

        If no key is provided, generates a cryptographically secure key.
        For new tokens, ensures they are inserted as new (not updated).
        """

        if not self.key:

            self.update_key()
            # For new objects, force INSERT to prevent overwriting existing tokens
            if self._state.adding:
                kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    def update_key(self):
        self.raw_key = self.generate_key()
        self.key = make_password(self.raw_key, hasher=MyPBKDF2PasswordHasher())

    @classmethod
    def generate_key(cls):
        return secrets.token_hex(48)

def __str__(self):
        return self.key


class TokenProxy(Token):
    """
    Proxy mapping pk to user pk for use in admin.
    """
    @property
    def pk(self):
        return self.user_id

    class Meta:
        proxy = 'hashed_auth.apps.AuthTokenConfig' in settings.INSTALLED_APPS
        abstract = 'hashed_auth.apps.AuthTokenConfig' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")