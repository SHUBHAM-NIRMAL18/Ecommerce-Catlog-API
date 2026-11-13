from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("catalog.api.urls")),
    # Product images from data/images, e.g. GET /images/p001-1.jpg.
    # Django's static view is enough for this app; a CDN or WhiteNoise would serve them in production.
    re_path(r"^images/(?P<path>.+)$", serve, {"document_root": settings.IMAGES_DIR}),
]

handler404 = "catalog.api.errors.not_found"
handler500 = "catalog.api.errors.server_error"
