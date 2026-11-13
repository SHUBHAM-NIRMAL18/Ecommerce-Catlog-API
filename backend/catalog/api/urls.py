from django.urls import path, re_path

from . import views
from .errors import not_found

urlpatterns = [
    path("health", views.health),
    # Any other /api/... path: JSON 404 in the same error shape (also when DEBUG is on).
    re_path(r"^.*$", not_found),
]
