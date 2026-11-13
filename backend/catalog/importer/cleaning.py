"""Turn raw catalog.json into clean rows for the database.

Pure Python with no database access, so it can be unit-tested on its own.

- Problems that can be fixed safely are fixed and recorded in `fixes`.
- Things left as they are (and handled by the API or UI) are recorded in `notes`.
- Problems that can't be fixed (broken references, duplicate ids, impossible
  values) raise CatalogError before a single row is written.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

STATUSES = {"active", "draft", "archived"}


class CatalogError(Exception):
    def __init__(self, errors):
        self.errors = errors
        lines = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"{len(errors)} problem(s) in catalog.json:\n{lines}")


@dataclass
class CleanCatalog:
    brands: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    products: list = field(default_factory=list)
    variants: list = field(default_factory=list)
    images: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    collections: list = field(default_factory=list)
    collection_items: list = field(default_factory=list)
    fixes: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def parse_datetime(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"date without timezone: {value!r}")
    return parsed


def average_rating(ratings):
    """Average rounded to one decimal, None when there are no ratings.

    Uses float round() because that is how catalog.json computed ratingAverage:
    exact ties go to even (4.25 -> 4.2) while 3.85, which is slightly above 3.85
    as a float, goes up (3.9). Decimal rounding would report false mismatches.
    """
    if not ratings:
        return None
    return Decimal(str(round(sum(ratings) / len(ratings), 1)))


def normalize_tags(tags):
    """Trim, lowercase and dedupe tags, keeping their order. Returns (tags, list of changes)."""
    result, changes = [], []
    for tag in tags or []:
        normalized = " ".join(str(tag).split()).lower()
        if normalized != tag:
            changes.append(f"{tag!r} -> {normalized!r}")
        if not normalized:
            continue
        if normalized in result:
            changes.append(f"duplicate {normalized!r} removed")
            continue
        result.append(normalized)
    return result, changes


def drop_null_attributes(attributes):
    """Missing and null mean the same thing, so null-valued keys are dropped."""
    attributes = attributes or {}
    kept = {key: value for key, value in attributes.items() if value is not None}
    dropped = [key for key, value in attributes.items() if value is None]
    return kept, dropped


def build_search_text(*parts):
    """Lowercased, whitespace-collapsed text that `q` search matches against."""
    words = []
    for part in parts:
        if isinstance(part, (list, tuple)):
            words.extend(str(p) for p in part)
        elif part:
            words.append(str(part))
    return " ".join(" ".join(words).split()).lower()


def _find_duplicates(values):
    return sorted(value for value, count in Counter(values).items() if count > 1)


def clean_catalog(raw):
    out = CleanCatalog()
    errors = []

    raw_brands = raw.get("brands") or []
    raw_categories = raw.get("categories") or []
    raw_products = raw.get("products") or []
    raw_reviews = raw.get("reviews") or []
    raw_collections = raw.get("collections") or []

    for label, items, key in [
        ("brand id", raw_brands, "id"),
        ("brand slug", raw_brands, "slug"),
        ("category id", raw_categories, "id"),
        ("category slug", raw_categories, "slug"),
        ("product id", raw_products, "id"),
        ("product slug", raw_products, "slug"),
        ("review id", raw_reviews, "id"),
        ("collection id", raw_collections, "id"),
        ("collection slug", raw_collections, "slug"),
    ]:
        for duplicate in _find_duplicates(item.get(key) for item in items):
            errors.append(f"duplicate {label}: {duplicate!r}")
    for duplicate in _find_duplicates(v.get("sku") for p in raw_products for v in p.get("variants") or []):
        errors.append(f"duplicate variant sku: {duplicate!r}")

    # Brands
    brands_by_id = {}
    for b in raw_brands:
        row = {"source_id": b["id"], "slug": b["slug"], "name": b["name"].strip(), "country": (b.get("country") or "").strip()}
        brands_by_id[b["id"]] = row
        out.brands.append(row)

    # Categories
    categories_by_id = {c["id"]: c for c in raw_categories}
    for c in raw_categories:
        parent = c.get("parentId")
        if parent is not None and parent not in categories_by_id:
            errors.append(f"category {c['id']}: unknown parentId {parent!r}")
        if parent == c["id"]:
            errors.append(f"category {c['id']}: is its own parent")
        out.categories.append({"source_id": c["id"], "slug": c["slug"], "name": c["name"].strip(), "parent": parent})

    # Reviews first, so product ratings can be recomputed from them.
    known_products = {p["id"] for p in raw_products}
    ratings_by_product = defaultdict(list)
    for r in raw_reviews:
        if r.get("productId") not in known_products:
            errors.append(f"review {r['id']}: unknown productId {r.get('productId')!r}")
            continue
        rating = r.get("rating")
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            errors.append(f"review {r['id']}: rating {rating!r} is not 1-5")
            continue
        body = (r.get("body") or "").strip() or None
        created = parse_datetime(r["createdAt"])
        ratings_by_product[r["productId"]].append(rating)
        out.reviews.append({
            "source_id": r["id"],
            "product": r["productId"],
            "rating": rating,
            "title": (r.get("title") or "").strip(),
            "body": body,
            "verified_purchase": bool(r.get("verifiedPurchase")),
            "helpful_count": max(int(r.get("helpfulCount") or 0), 0),
            "created_at": created,
            "updated_at": created,
        })
    reviews_without_body = sum(1 for r in out.reviews if r["body"] is None)
    if reviews_without_body:
        out.notes.append(f"{reviews_without_body} reviews have no body: stored as null, the UI shows only the title")

    # Products, variants, images
    dropped_attributes = Counter()
    for p in raw_products:
        pid = p["id"]
        brand = brands_by_id.get(p.get("brandId"))
        category = categories_by_id.get(p.get("categoryId"))
        if brand is None:
            errors.append(f"product {pid}: unknown brandId {p.get('brandId')!r}")
        if category is None:
            errors.append(f"product {pid}: unknown categoryId {p.get('categoryId')!r}")
        if p.get("status") not in STATUSES:
            errors.append(f"product {pid}: unknown status {p.get('status')!r}")
        if brand is None or category is None:
            continue

        attributes, dropped = drop_null_attributes(p.get("attributes"))
        dropped_attributes.update(dropped)

        tags, tag_changes = normalize_tags(p.get("tags"))
        if tag_changes:
            out.fixes.append(f"product {pid}: tags normalized ({', '.join(tag_changes)})")
        features = [f.strip() for f in p.get("features") or [] if f and f.strip()]

        prices, any_stock = [], False
        for v in p.get("variants") or []:
            sku = v.get("sku")
            price = money(v["price"]) if v.get("price") is not None else None
            stock = v.get("stock")
            if price is None or price <= 0:
                errors.append(f"variant {sku}: price {v.get('price')!r} must be > 0")
                continue
            if not isinstance(stock, int) or stock < 0:
                errors.append(f"variant {sku}: stock {stock!r} must be >= 0")
                continue
            compare_at = money(v["compareAtPrice"]) if v.get("compareAtPrice") is not None else None
            if compare_at is not None and compare_at <= price:
                out.fixes.append(
                    f"variant {sku}: compareAtPrice {compare_at} is not above price {price}; "
                    "set to null so it is not shown as a sale (R5)"
                )
                compare_at = None
            options = v.get("options") or {}
            prices.append(price)
            any_stock = any_stock or stock > 0
            out.variants.append({
                "product": pid,
                "sku": sku,
                "color": (options.get("color") or "").strip(),
                "size": (options.get("size") or "").strip(),
                "price": price,
                "compare_at_price": compare_at,
                "stock": stock,
            })
        if not prices:
            out.notes.append(f"product {pid}: has no variants, so it has no price and is not in stock")
        elif not any_stock:
            out.notes.append(f"product {pid}: every variant has stock 0, shown as sold out (R3)")

        images = [i for i in p.get("images") or [] if i and i.get("url")]
        if not images:
            out.notes.append(f"product {pid}: has no images, the UI shows a placeholder")
        for position, image in enumerate(images):
            out.images.append({
                "product": pid,
                "url": image["url"].strip(),
                "alt": (image.get("alt") or p["name"]).strip(),
                "position": position,
            })

        ratings = ratings_by_product.get(pid, [])
        rating_average = average_rating(ratings)
        given_average = Decimal(str(p["ratingAverage"])) if p.get("ratingAverage") is not None else None
        if (given_average, p.get("reviewCount")) != (rating_average, len(ratings)):
            out.fixes.append(
                f"product {pid}: rating {given_average}/{p.get('reviewCount')} reviews in the file, "
                f"recomputed from reviews as {rating_average}/{len(ratings)}"
            )

        parent = categories_by_id.get(category.get("parentId")) if category.get("parentId") else None
        out.products.append({
            "source_id": pid,
            "slug": p["slug"],
            "name": p["name"].strip(),
            "description": (p.get("description") or "").strip(),
            "brand": p["brandId"],
            "category": p["categoryId"],
            "status": p.get("status"),
            "tags": tags,
            "features": features,
            "attributes": attributes,
            "rating_average": rating_average,
            "review_count": len(ratings),
            "views": max(int(p.get("views") or 0), 0),
            "sales_count": max(int(p.get("salesCount") or 0), 0),
            "min_price": min(prices) if prices else None,
            "in_stock": any_stock,
            "search_text": build_search_text(
                p["name"], p.get("description"), brand["name"], category["name"],
                parent["name"] if parent else None, attributes.get("material"), tags,
            ),
            "created_at": parse_datetime(p["createdAt"]),
            "updated_at": parse_datetime(p.get("updatedAt") or p["createdAt"]),
        })

    used_categories = {p["categoryId"] for p in raw_products}
    for c in raw_categories:
        if c.get("parentId") is not None and c["id"] not in used_categories:
            out.notes.append(f"category {c['slug']}: has no products; the API returns productCount 0")

    if dropped_attributes:
        detail = ", ".join(f"{key} x{count}" for key, count in dropped_attributes.most_common())
        out.fixes.append(
            f"attributes: dropped {sum(dropped_attributes.values())} null values ({detail}); "
            "missing and null mean the same thing"
        )

    # Collections
    statuses = {p["id"]: p.get("status") for p in raw_products}
    for c in raw_collections:
        starts, ends = parse_datetime(c.get("startsAt")), parse_datetime(c.get("endsAt"))
        if starts and ends and ends <= starts:
            errors.append(f"collection {c['slug']}: endsAt is not after startsAt")
        out.collections.append({
            "source_id": c["id"],
            "slug": c["slug"],
            "name": c["name"].strip(),
            "description": (c.get("description") or "").strip(),
            "is_active": bool(c.get("isActive")),
            "starts_at": starts,
            "ends_at": ends,
        })
        seen = []
        for product_id in c.get("productIds") or []:
            if product_id not in known_products:
                out.fixes.append(f"collection {c['slug']}: unknown product {product_id} skipped")
            elif product_id in seen:
                out.fixes.append(f"collection {c['slug']}: duplicate product {product_id} removed")
            else:
                seen.append(product_id)
        for position, product_id in enumerate(seen):
            out.collection_items.append({"collection": c["id"], "product": product_id, "position": position})
        hidden = [pid for pid in seen if statuses.get(pid) != "active"]
        if hidden:
            out.notes.append(
                f"collection {c['slug']}: contains non-active products {', '.join(hidden)}; the API hides them (R1)"
            )
        if not c.get("isActive"):
            out.notes.append(f"collection {c['slug']}: isActive is false; the API hides it (R4)")

    if errors:
        raise CatalogError(errors)
    return out
