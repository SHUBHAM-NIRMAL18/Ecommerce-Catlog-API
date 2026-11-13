from django.contrib import admin

from .models import (
    Brand,
    Category,
    Collection,
    CollectionItem,
    Product,
    ProductImage,
    ProductVariant,
    Review,
)


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
    list_display = ["name", "brand", "category", "status", "min_price", "in_stock", "rating_average", "review_count"]
    list_filter = ["status", "in_stock", "brand", "category"]
    search_fields = ["name", "slug", "source_id"]
    list_select_related = ["brand", "category"]
    inlines = [ProductVariantInline, ProductImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "rating", "verified_purchase", "helpful_count", "created_at"]
    list_filter = ["rating", "verified_purchase"]
    search_fields = ["title", "body", "product__name"]
    list_select_related = ["product"]
    raw_id_fields = ["product"]


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 0
    raw_id_fields = ["product"]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "starts_at", "ends_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    inlines = [CollectionItemInline]
