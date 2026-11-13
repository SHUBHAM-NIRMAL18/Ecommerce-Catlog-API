from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .base import SourcedModel


class CollectionQuerySet(models.QuerySet):
    def live(self, at=None):
        """Active collections whose optional date window contains `at` (default: now)."""
        at = at or timezone.now()
        return self.filter(
            Q(is_active=True),
            Q(starts_at__isnull=True) | Q(starts_at__lte=at),
            Q(ends_at__isnull=True) | Q(ends_at__gte=at),
        )


class Collection(SourcedModel):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    products = models.ManyToManyField(
        "catalog.Product", through="catalog.CollectionItem", related_name="collections"
    )

    objects = CollectionQuerySet.as_manager()

    class Meta:
        db_table = "collection"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(starts_at__isnull=True) | Q(ends_at__isnull=True) | Q(ends_at__gt=F("starts_at")),
                name="collection_ends_after_starts",
            ),
        ]

    def __str__(self):
        return self.name


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="collection_items")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "collection_item"
        ordering = ["collection_id", "position"]
        constraints = [
            models.UniqueConstraint(fields=["collection", "product"], name="collection_item_unique_product"),
            models.UniqueConstraint(fields=["collection", "position"], name="collection_item_unique_position"),
        ]

    def __str__(self):
        return f"{self.collection_id} #{self.position}"
