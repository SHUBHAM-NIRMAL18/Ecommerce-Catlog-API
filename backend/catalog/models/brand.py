from django.db import models

from .base import SourcedModel


class Brand(SourcedModel):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = "brand"
        ordering = ["name"]

    def __str__(self):
        return self.name
