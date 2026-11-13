from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at.

    Defaults to now() instead of auto_now_add / auto_now so the seed can keep
    the real dates from catalog.json; auto_now would overwrite them on save.
    """

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class SourcedModel(TimeStampedModel):
    """A row imported from catalog.json, upserted by its JSON id."""

    source_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Id from catalog.json (e.g. 'b01'); used by the seed for idempotent upserts.",
    )

    class Meta:
        abstract = True
