from django.contrib import admin

from .models import Brand, Category, Product, ProductImage, ProductVariant


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "country"]
    search_fields = ["name", "slug"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["sku", "color", "size", "price", "compare_at_price", "stock"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ["position", "url", "alt"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "brand", "category", "status", "rating_average", "review_count"]
    list_filter = ["status", "brand", "category"]
    search_fields = ["name", "slug", "source_id"]
    list_select_related = ["brand", "category"]
    inlines = [ProductVariantInline, ProductImageInline]
