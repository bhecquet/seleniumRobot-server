
from django.conf.urls import url, include
from rest_framework import routers
from elementInfoServer.views import viewsets
from elementInfoServer.views.api import ElementInfoList


router = routers.DefaultRouter()
router.register(r'elementinfo', viewsets.ElementInfoViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls), name='api'),
    url(r'^api/elementinfos', ElementInfoList.as_view(), name='elementInfoApi'),
]
