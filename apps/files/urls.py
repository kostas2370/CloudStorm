from django.urls import path

from .views import SecureAzureBlobView, FilesViewSet, GuestTaskView
from rest_framework import routers

app_name = "files"

router = routers.DefaultRouter()

router.register("files", FilesViewSet, "files")

urlpatterns = [
    path(
        "files/media/<str:group_name>/<str:filename>/",
        SecureAzureBlobView.as_view(),
        name="secure-azure-file",
    ),

    path("guest_task/", GuestTaskView.as_view(), name = "guest_task", ),
]


urlpatterns += router.urls
