
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import include, path

from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView
from rest_framework import HTTP_HEADER_ENCODING, exceptions, permissions, renderers, status


from django.test import TestCase, override_settings

from hashed_auth.authentication import TokenAuthentication
from hashed_auth.models import Token
from hashed_auth.views import obtain_auth_token


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def put(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


urlpatterns = [

    path(
        'token/',
        MockView.as_view(authentication_classes=[TokenAuthentication])
    ),

    path('auth-token/', obtain_auth_token),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]


@override_settings(ROOT_URLCONF=__name__)
class TokenAuthTests(TestCase):
    model = Token
    path = '/token/'
    header_prefix = 'Token '

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.username_no_token = 'john_no_token'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )
        self.user_no_token = User.objects.create_user(
            self.username_no_token, self.email, self.password
        )

        self.token = self.model.objects.create(user=self.user)
        self.key = self.token.raw_key

    def test_post_form_passing_token_auth(self):
        """
        Ensure POSTing json over token auth with correct
        credentials passes and does not require CSRF
        """
        auth = self.header_prefix + self.key
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_fail_authentication_if_user_is_not_active(self):
        user = User.objects.create_user('foo', 'bar', 'baz')
        user.is_active = False
        user.save()
        self.model.objects.create(key='foobar_token', user=user)
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix + 'foobar_token'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_form_passing_nonexistent_token_auth(self):
        # use a nonexistent token key
        auth = self.header_prefix + 'wxyz6789'
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_if_token_is_missing(self):
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_if_token_contains_spaces(self):
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix + 'foo bar'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_form_passing_invalid_token_auth(self):
        # add an 'invalid' unicode character
        auth = self.header_prefix + self.key + "¸"
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_json_passing_token_auth(self):
        """
        Ensure POSTing form over token auth with correct
        credentials passes and does not require CSRF
        """
        auth = self.header_prefix + self.key
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            format='json', HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_post_json_makes_one_db_query(self):
        """
        Ensure that authenticating a user using a
        token performs only one DB query
        """
        auth = self.header_prefix + self.key

        def func_to_test():
            return self.csrf_client.post(
                self.path, {'example': 'example'},
                format='json', HTTP_AUTHORIZATION=auth
            )

        self.assertNumQueries(1, func_to_test)

    def test_post_form_failing_token_auth(self):
        """
        Ensure POSTing form over token auth without correct credentials fails
        """
        response = self.csrf_client.post(self.path, {'example': 'example'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_json_failing_token_auth(self):
        """
        Ensure POSTing json over token auth without correct credentials fails
        """
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_has_auto_assigned_key_if_none_provided(self):
        """Ensure creating a token with no key will auto-assign a key"""
        self.token.delete()
        token = self.model.objects.create(user=self.user)
        assert bool(token.key)

    def test_generate_key_returns_string(self):
        """Ensure generate_key returns a string"""
        token = self.model()
        key = token.generate_key()
        assert isinstance(key, str)

    def test_generate_key_accessible_as_classmethod(self):
        key = self.model.generate_key()
        assert isinstance(key, str)

    def test_generate_key_returns_valid_format(self):
        """Ensure generate_key returns a valid token format"""
        key = self.model.generate_key()
        assert len(key) == 96
        # Should contain only valid hexadecimal characters
        assert all(c in '0123456789abcdef' for c in key)

    def test_generate_key_produces_unique_values(self):
        """Ensure generate_key produces unique values across multiple calls"""
        keys = set()
        for _ in range(100):
            key = self.model.generate_key()
            assert key not in keys, f"Duplicate key generated: {key}"
            keys.add(key)

    def test_generate_key_collision_resistance(self):
        """Test collision resistance with reasonable sample size"""
        keys = set()
        for _ in range(500):
            key = self.model.generate_key()
            assert key not in keys, f"Collision found: {key}"
            keys.add(key)
        assert len(keys) == 500, f"Expected 500 unique keys, got {len(keys)}"

    def test_generate_key_randomness_quality(self):
        """Test basic randomness properties of generated keys"""
        keys = [self.model.generate_key() for _ in range(10)]
        # Consecutive keys should be different
        for i in range(len(keys) - 1):
            assert keys[i] != keys[i + 1], "Consecutive keys should be different"
        # Keys should not follow obvious patterns
        for key in keys:
            # Should not be all same character
            assert not all(c == key[0] for c in key), f"Key has all same characters: {key}"

    def test_token_login_json(self):
        """Ensure token login view using JSON POST works."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username_no_token, 'password': self.password},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

    def test_token_login_json_bad_creds(self):
        """
        Ensure token login view using JSON POST fails if
        bad credentials are used
        """
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username, 'password': "badpass"},
            format='json'
        )
        assert response.status_code == 400

    def test_token_login_json_missing_fields(self):
        """Ensure token login view using JSON POST fails if missing fields."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               {'username': self.username}, format='json')
        assert response.status_code == 400

    def test_token_login_form(self):
        """Ensure token login view using form POST works."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username_no_token, 'password': self.password}
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

        assert Token.objects.get(user=self.user_no_token).key.startswith("pbkdf2_sha256$")

    def test_token_login_form_existing_token(self):
        """If token has already been created, do not create it an other time"""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username, 'password': self.password}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'token has already been created previously'

    def test_update_token_login_form_existing_token(self):
        """If token has already been created, do not create it an other time"""

        client = APIClient(enforce_csrf_checks=True)
        response = client.patch(
            '/auth-token/',
            {'username': self.username, 'password': self.password}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['token'] != self.key
