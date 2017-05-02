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
from django.conf.urls import url, include
from rest_framework import routers
from snapshotServer import views
from django.contrib import admin
from snapshotServer.views import FileUploadView

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'snapshot', views.SnapshotViewSet)
router.register(r'application', views.ApplicationViewSet)
router.register(r'version', views.VersionViewSet)
router.register(r'testcase', views.TestCaseViewSet) 
router.register(r'environment', views.TestEnvironmentViewSet)
router.register(r'teststep', views.TestStepViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'session', views.TestSessionViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
