from django.contrib import admin
from django.urls import path, include


from django.conf import settings
from django.conf.urls.static import static
from CloudStorm import views as error_views  # Adjust if needed
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


handler404 = error_views.custom_404
handler500 = error_views.custom_500

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.groups.urls")),
    path("api/", include("apps.files.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
