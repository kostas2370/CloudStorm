from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Cloudstorm API Documentation ",
        default_version='v1',
        description="Docs ",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="kostas2372@gmail.com"),
        license=openapi.License(name="Cloudstorm License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout = 0), name = 'schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.groups.urls')),
    path('api/', include('apps.files.urls')),
]
