from rest_framework import routers

from .views import *

app_name = "groups"

router = routers.DefaultRouter()
router.register('groups', GroupsViewSet)

urlpatterns = []

urlpatterns += router.urls
