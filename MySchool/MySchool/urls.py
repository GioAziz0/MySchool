from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.api.urls")),
    path("api/schools/<slug:school_slug>/", include("core.api.urls")),
    path("", include("users.web_urls")),
    path("", include("core.web_urls")),
]
