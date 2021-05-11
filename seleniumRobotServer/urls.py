"""seleniumRobotServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls.conf import path
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
    
    url(r'^api-token-auth/', CustomAuthToken.obtain_auth_token),
    path('admin/login/', views.LoginView.as_view()),
    path('admin/', admin.site.urls),
    url(r'^snapshot/', include('snapshotServer.urls')),
    url(r'^variable/', include('variableServer.urls')),
    url(r'^elementinfo/', include('elementInfoServer.urls')),
    url(r'^commons/', include('commonsServer.urls')),
    url(r'^oidc/', include('mozilla_django_oidc.urls')),
    url(r'^health/', include('health_check.urls')),
    
    path('accounts/login/', csrf_exempt(ensure_csrf_cookie(xframe_options_exempt(views.LoginView.as_view()))), name='login'),
    
    # add media directory
] +   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
