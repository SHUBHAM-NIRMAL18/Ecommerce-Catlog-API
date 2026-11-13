from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import F, Q

from .base import SourcedModel, TimeStampedModel


class Product(SourcedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DRAFT = "draft", "Draft"
        ARCHIVED = "archived", "Archived"

    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    brand = models.ForeignKey("catalog.Brand", on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey("catalog.Category", on_delete=models.PROTECT, related_name="products")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    features = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    # Category-specific facts (material, weightKg, dimmable, ...). Keys with a null
    # value are dropped by the seed, so "missing" and "null" mean the same thing.
    attributes = models.JSONField(default=dict, blank=True)

    # Denormalised for fast sorting; the seed recomputes them from reviews.
    rating_average = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)

    # Listing fields derived from variants and relations; the seed keeps them in sync.
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Lowest variant price (R2). Used for price filters and sorting.",
    )
    in_stock = models.BooleanField(default=False, help_text="True if any variant has stock > 0 (R3).")
    search_text = models.TextField(
        blank=True, editable=False,
        help_text="Lowercased name, description, brand, categories, material and tags for `q` search.",
    )

    class Meta:
        db_table = "product"
        ordering = ["-created_at"]
        # Every public query filters status='active' (R1), so the indexes are partial:
        # smaller, and they skip draft/archived rows. `id` is the tiebreaker for stable paging.
        indexes = [
            GinIndex(
                fields=["search_text"], opclasses=["gin_trgm_ops"],
                name="product_search_trgm", condition=Q(status="active"),
            ),
            models.Index(fields=["min_price", "id"], name="product_price", condition=Q(status="active")),
            models.Index(fields=["-created_at", "id"], name="product_newest", condition=Q(status="active")),
            models.Index(
                F("rating_average").desc(nulls_last=True), F("id"),
                name="product_rating", condition=Q(status="active"),
            ),
            models.Index(fields=["-sales_count", "id"], name="product_popular", condition=Q(status="active")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating_average__isnull=True) | Q(rating_average__gte=1, rating_average__lte=5),
                name="product_rating_average_1_to_5",
            ),
            models.CheckConstraint(
                condition=Q(review_count=0, rating_average__isnull=True)
                | Q(review_count__gt=0, rating_average__isnull=False),
                name="product_rating_matches_review_count",
            ),
        ]

    def __str__(self):
        return self.name


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=40, unique=True)
    color = models.CharField(max_length=60)
    size = models.CharField(max_length=60)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_variant"
        ordering = ["product_id", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name="variant_price_positive"),
            models.CheckConstraint(
                condition=Q(compare_at_price__isnull=True) | Q(compare_at_price__gt=F("price")),
                name="variant_compare_at_above_price",
            ),
            models.UniqueConstraint(
                fields=["product", "color", "size"], name="variant_unique_options_per_product"
            ),
        ]

    def __str__(self):
        return self.sku


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    url = models.CharField(max_length=255, help_text="Path relative to the data folder, e.g. images/p001-1.jpg")
    alt = models.CharField(max_length=255, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "product_image"
        ordering = ["product_id", "position"]
        constraints = [
            models.UniqueConstraint(fields=["product", "position"], name="image_unique_position_per_product"),
        ]

    def __str__(self):
        return self.url
