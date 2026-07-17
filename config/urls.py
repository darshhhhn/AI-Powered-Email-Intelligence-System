"""Root URL configuration for Mail Viewer."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("mail_app.urls")),
]
