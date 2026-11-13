from django.db import models
from django.db.models import Q

from .base import SourcedModel


class Review(SourcedModel):
    # db_index=False: the (product, -created_at) index below already covers product lookups.
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="reviews", db_index=False
    )
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    body = models.TextField(null=True, blank=True)  # 68 reviews in the data have no body
    verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "review"
        ordering = ["-created_at"]
        indexes = [
            # Reviews endpoint: WHERE product_id = ? ORDER BY created_at DESC
            models.Index(fields=["product", "-created_at"], name="review_product_newest"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"),
        ]

    def __str__(self):
        return f"{self.rating}★ {self.title}"
