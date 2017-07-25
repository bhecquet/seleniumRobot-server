
from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers
from variableServer.views import varActionView

router = routers.DefaultRouter()

urlpatterns = [
    url(r'^api/', include(router.urls), name='api'),
    url(r'copyVariables', varActionView.copyVariables, name='copyVariables'),
    url(r'changeVariables', varActionView.changeVariables, name='changeVariables'),
]
