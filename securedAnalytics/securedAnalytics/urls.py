"""
URL configuration for securedAnalytics project.

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Secured Analytics Administration"
admin.site.site_title = "Secured Analytics Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("securedAnalyticsApp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
