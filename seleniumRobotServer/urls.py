
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth import views
from django.urls.conf import path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from commonsServer.views.api import CustomAuthToken

# in case openid is configured for login, change login page
views.LoginView.site_header = 'Selenium Server administration'
if ('mozilla_django_oidc.auth.OIDCAuthenticationBackend' in settings.AUTHENTICATION_BACKENDS
    or 'seleniumRobotServer.openidbackend.NameOIDCAB' in settings.AUTHENTICATION_BACKENDS):
    views.LoginView.template_name = 'admin/login_with_openid.html'
else:
    views.LoginView.template_name = 'admin/login.html'

urlpatterns = [
    
    re_path(r'^api-token-auth/', CustomAuthToken.obtain_auth_token),
    path('admin/login/', views.LoginView.as_view()),
    path('admin/', admin.site.urls),
    re_path(r'^snapshot/', include('snapshotServer.urls')),
    re_path(r'^variable/', include('variableServer.urls')),
    re_path(r'^elementinfo/', include('elementInfoServer.urls')),
    re_path(r'^commons/', include('commonsServer.urls')),
    re_path(r'^oidc/', include('mozilla_django_oidc.urls')),
    
    path('accounts/login/', csrf_exempt(ensure_csrf_cookie(xframe_options_exempt(views.LoginView.as_view()))), name='login'),
    
    # add media directory
] #+   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
