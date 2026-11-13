from django.contrib import admin

from .models import Brand, Category


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "country"]
    search_fields = ["name", "slug"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]
