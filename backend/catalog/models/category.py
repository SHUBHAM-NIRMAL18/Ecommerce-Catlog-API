from django.db import models

from .base import SourcedModel


class Category(SourcedModel):
    """Two-level tree: main categories have no parent, sub-categories point to one."""

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "category"
        ordering = ["name"]
        verbose_name_plural = "categories"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(parent=models.F("id")),
                name="category_not_own_parent",
            ),
        ]

    def __str__(self):
        return self.name
