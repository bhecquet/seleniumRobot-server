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
from commonsServer.views.api import CustomAuthToken
from django.urls.conf import path

urlpatterns = [
    
    url(r'^api-token-auth/', CustomAuthToken.obtain_auth_token),
    url(r'^admin/', admin.site.urls),
    url(r'^snapshot/', include('snapshotServer.urls')),
    url(r'^variable/', include('variableServer.urls')),
    url(r'^elementinfo/', include('elementInfoServer.urls')),
    url(r'^commons/', include('commonsServer.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # add media directory
] +   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
