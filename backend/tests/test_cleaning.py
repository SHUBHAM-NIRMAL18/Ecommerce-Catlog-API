"""Unit tests for the data-quality rules in catalog.importer.cleaning (no database)."""

from decimal import Decimal

import pytest

from catalog.importer.cleaning import (
    CatalogError,
    average_rating,
    clean_catalog,
    drop_null_attributes,
    normalize_tags,
)


def make_catalog(**overrides):
    """A tiny valid catalog; tests change only the part they care about."""
    product = {
        "id": "p1", "slug": "rug", "name": "Rug", "description": "A rug.",
        "brandId": "b1", "categoryId": "c2", "status": "active",
        "tags": ["wool"], "features": [], "attributes": {"material": "Wool"},
        "images": [], "ratingAverage": None, "reviewCount": 0, "views": 0, "salesCount": 0,
        "createdAt": "2025-01-01T00:00:00Z", "updatedAt": "2025-01-02T00:00:00Z",
        "variants": [{"sku": "S1", "options": {"color": "Red", "size": "M"},
                      "price": 50.0, "compareAtPrice": None, "stock": 1}],
    }
    product.update(overrides.pop("product", {}))
    catalog = {
        "brands": [{"id": "b1", "slug": "acme", "name": "Acme", "country": "NP"}],
        "categories": [
            {"id": "c1", "slug": "textiles", "name": "Textiles", "parentId": None},
            {"id": "c2", "slug": "rugs", "name": "Rugs", "parentId": "c1"},
        ],
        "products": [product],
        "reviews": [],
        "collections": [],
    }
    catalog.update(overrides)
    return catalog


def test_null_and_missing_attributes_are_the_same():
    kept, dropped = drop_null_attributes({"material": "Wool", "care": None})
    assert kept == {"material": "Wool"}
    assert dropped == ["care"]
    assert "care" not in kept  # same result as if the key were never there


def test_tags_are_trimmed_lowercased_and_deduped():
    tags, changes = normalize_tags(["Washable ", "linen", "Linen", "LED"])
    assert tags == ["washable", "linen", "led"]
    assert len(changes) == 4  # 3 rewrites + 1 duplicate removed


def test_compare_at_price_not_above_price_is_dropped():
    clean = clean_catalog(make_catalog(product={"variants": [
        {"sku": "S1", "options": {"color": "Red", "size": "M"}, "price": 39.0, "compareAtPrice": 34.0, "stock": 1},
    ]}))
    assert clean.variants[0]["compare_at_price"] is None
    assert any("S1" in fix for fix in clean.fixes)


def test_list_price_and_stock_come_from_variants():
    clean = clean_catalog(make_catalog(product={"variants": [
        {"sku": "S1", "options": {"color": "Red", "size": "L"}, "price": 559.0, "compareAtPrice": None, "stock": 0},
        {"sku": "S2", "options": {"color": "Red", "size": "M"}, "price": 349.0, "compareAtPrice": None, "stock": 0},
    ]}))
    product = clean.products[0]
    assert product["min_price"] == Decimal("349.00")  # R2: lowest variant price
    assert product["in_stock"] is False  # R3: no variant has stock


def test_duplicate_product_in_collection_is_removed():
    clean = clean_catalog(make_catalog(collections=[{
        "id": "col1", "slug": "winter", "name": "Winter", "description": "",
        "isActive": True, "startsAt": None, "endsAt": None, "productIds": ["p1", "p1"],
    }]))
    assert len(clean.collection_items) == 1
    assert any("duplicate product p1" in fix for fix in clean.fixes)


def test_rating_rounding_matches_catalog_json():
    assert average_rating([]) is None
    assert average_rating([4, 3, 5, 5]) == Decimal("4.2")  # 4.25, as stored for p008
    assert average_rating([4] * 17 + [3] * 3) == Decimal("3.9")  # 3.85, as stored for p006


def test_broken_reference_stops_the_seed_before_writing():
    with pytest.raises(CatalogError) as exc:
        clean_catalog(make_catalog(product={"brandId": "missing"}))
    assert "unknown brandId 'missing'" in str(exc.value)
