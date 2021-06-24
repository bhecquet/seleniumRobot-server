
from django.conf.urls import include
from rest_framework import routers
from elementInfoServer.views import viewsets
from elementInfoServer.views.api import ElementInfoList
from django.urls import re_path


router = routers.DefaultRouter()
router.register(r'elementinfo', viewsets.ElementInfoViewSet)

urlpatterns = [
    re_path(r'^api/', include(router.urls), name='api'),
    re_path(r'^api/elementinfos', ElementInfoList.as_view(), name='elementInfoApi'),
]
