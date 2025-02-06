from django.urls import path

from .views import *
from rest_framework import routers

app_name = "files"

router = routers.DefaultRouter()

router.register('files', GroupsViewSet, "files")

urlpatterns = []

urlpatterns += router.urls
