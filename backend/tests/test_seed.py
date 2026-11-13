"""Integration test: seed the real catalog.json into the test database."""

import io

import pytest
from django.core.management import call_command

from catalog.models import Product, ProductVariant, Review


def counts():
    return Product.objects.count(), ProductVariant.objects.count(), Review.objects.count()


@pytest.mark.django_db
def test_seed_imports_catalog_and_is_idempotent():
    call_command("seed", stdout=io.StringIO())
    assert counts() == (120, 336, 933)
    ids = list(Product.objects.order_by("id").values_list("id", flat=True))

    call_command("seed", stdout=io.StringIO())
    assert counts() == (120, 336, 933)
    # Same rows were updated in place, not deleted and recreated.
    assert list(Product.objects.order_by("id").values_list("id", flat=True)) == ids
