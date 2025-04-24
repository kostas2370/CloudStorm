from django.urls import path

from .views import *
from rest_framework import routers

app_name = "files"

router = routers.DefaultRouter()

router.register('files', GroupsViewSet, "files")

urlpatterns = [path('files/<str:group_name>/<str:filename>/', SecureAzureBlobView.as_view(), name='secure-azure-file'),]


urlpatterns += router.urls
