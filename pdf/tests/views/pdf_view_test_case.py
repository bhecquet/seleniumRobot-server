from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase


class PdfViewTestCase(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('user', password='pwd')

    def login(self):
        self.client.force_login(self.user)
