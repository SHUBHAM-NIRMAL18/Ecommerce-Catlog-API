from django.urls import path, re_path

from . import views
from .errors import not_found

urlpatterns = [
    path("health", views.health),
    path("products", views.product_list),
    path("products/<slug:slug>", views.product_detail),
    path("products/<slug:slug>/reviews", views.product_reviews),
    path("products/<slug:slug>/similar", views.product_similar),
    # Any other /api/... path: JSON 404 in the same error shape (also when DEBUG is on).
    re_path(r"^.*$", not_found),
]
