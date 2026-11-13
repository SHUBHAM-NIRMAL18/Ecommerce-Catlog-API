"""Write a CleanCatalog to the database.

Idempotent: rows are upserted by their natural key (source_id, or sku for
variants), so running the seed again updates rows instead of duplicating them.
Rows for these products that are no longer in the file are removed.
Everything runs in one transaction: either the whole import succeeds or nothing changes.
"""

from django.db import transaction

from catalog.models import (
    Brand,
    Category,
    Collection,
    CollectionItem,
    Product,
    ProductImage,
    ProductVariant,
    Review,
)


def _upsert(model, rows, key, update_fields):
    """Insert rows, or update them when `key` already exists. Returns {key: id}."""
    if rows:
        model.objects.bulk_create(
            [model(**row) for row in rows],
            update_conflicts=True,
            unique_fields=[key],
            update_fields=update_fields,
            batch_size=500,
        )
    keys = [row[key] for row in rows]
    return dict(model.objects.filter(**{f"{key}__in": keys}).values_list(key, "id"))


@transaction.atomic
def load_catalog(clean):
    brand_ids = _upsert(Brand, clean.brands, "source_id", ["slug", "name", "country"])

    # Categories level by level, so a parent always exists before its children.
    category_ids = {}
    remaining = list(clean.categories)
    while remaining:
        ready = [c for c in remaining if c["parent"] is None or c["parent"] in category_ids]
        rows = [
            {**{k: v for k, v in c.items() if k != "parent"}, "parent_id": category_ids.get(c["parent"])}
            for c in ready
        ]
        category_ids |= _upsert(Category, rows, "source_id", ["slug", "name", "parent_id"])
        remaining = [c for c in remaining if c not in ready]

    product_rows = [
        {
            **{k: v for k, v in p.items() if k not in ("brand", "category")},
            "brand_id": brand_ids[p["brand"]],
            "category_id": category_ids[p["category"]],
        }
        for p in clean.products
    ]
    product_fields = [k for k in product_rows[0] if k != "source_id"] if product_rows else []
    product_ids = _upsert(Product, product_rows, "source_id", product_fields)
    seeded_products = list(product_ids.values())

    variant_rows = [
        {**{k: val for k, val in variant.items() if k != "product"}, "product_id": product_ids[variant["product"]]}
        for variant in clean.variants
    ]
    _upsert(
        ProductVariant, variant_rows, "sku",
        ["product_id", "color", "size", "price", "compare_at_price", "stock"],
    )
    ProductVariant.objects.filter(product_id__in=seeded_products).exclude(
        sku__in=[v["sku"] for v in clean.variants]
    ).delete()

    # Images have no id in the file, so they are replaced as a set.
    ProductImage.objects.filter(product_id__in=seeded_products).delete()
    ProductImage.objects.bulk_create([
        ProductImage(**{k: v for k, v in i.items() if k != "product"}, product_id=product_ids[i["product"]])
        for i in clean.images
    ])

    review_rows = [
        {**{k: v for k, v in r.items() if k != "product"}, "product_id": product_ids[r["product"]]}
        for r in clean.reviews
    ]
    _upsert(
        Review, review_rows, "source_id",
        ["product_id", "rating", "title", "body", "verified_purchase", "helpful_count", "created_at", "updated_at"],
    )
    Review.objects.filter(product_id__in=seeded_products).exclude(
        source_id__in=[r["source_id"] for r in clean.reviews]
    ).delete()

    collection_ids = _upsert(
        Collection, clean.collections, "source_id",
        ["slug", "name", "description", "is_active", "starts_at", "ends_at"],
    )
    # Collection items are a join table with no id of their own: replaced as a set.
    CollectionItem.objects.filter(collection_id__in=collection_ids.values()).delete()
    CollectionItem.objects.bulk_create([
        CollectionItem(
            collection_id=collection_ids[i["collection"]],
            product_id=product_ids[i["product"]],
            position=i["position"],
        )
        for i in clean.collection_items
    ])

    return {
        "brands": Brand.objects.count(),
        "categories": Category.objects.count(),
        "products": Product.objects.count(),
        "variants": ProductVariant.objects.count(),
        "images": ProductImage.objects.count(),
        "reviews": Review.objects.count(),
        "collections": Collection.objects.count(),
        "collection items": CollectionItem.objects.count(),
    }
