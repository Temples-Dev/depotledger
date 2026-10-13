"""Project URL routing. Domain routes land under api/v1/ per milestone."""

from django.contrib import admin
from django.urls import include, path

from .views import HealthCheckView, api_not_found

handler404 = api_not_found

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health"),
    path("api/v1/", include("apps.catalogue.urls")),
]
