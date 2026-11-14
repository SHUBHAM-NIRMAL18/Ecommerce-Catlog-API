"""API tests against the real seeded catalog.

Expected answers are computed independently from the raw catalog.json (the `catalog`
fixture), never copied from API output, so a wrong query can't make its own test pass.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from django.conf import settings
from django.utils import timezone

pytestmark = pytest.mark.django_db

SORTS = ["price_asc", "price_desc", "newest", "rating", "popular"]


# ---------- helpers ----------

def get(client, path, **params):
    return client.get(path, params)


def fetch_all(client, path, **params):
    """Every item from a paginated endpoint, page by page."""
    items, page = [], 1
    while True:
        body = get(client, path, limit=7, page=page, **params).json()
        items += body["items"]
        if page >= body["totalPages"]:
            return items, body["total"]
        page += 1


def active(catalog):
    return [p for p in catalog["products"] if p["status"] == "active"]


def lowest_price(product):
    return min(Decimal(str(v["price"])) for v in product["variants"])


def parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def norm_tags(tags):
    return list(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))


def assert_error(response, status, code, field=None):
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str) and error["message"]
    if field is not None:
        assert field in [d["field"] for d in error["details"]]


# ---------- errors and validation ----------

def test_validation_error_has_the_exact_error_shape(client):
    response = get(client, "/api/products", minPrice="abc")
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "minPrice: A valid number is required.",
            "details": [{"field": "minPrice", "value": "abc", "message": "A valid number is required."}],
        }
    }


@pytest.mark.parametrize("params, field", [
    ({"minPrice": "abc"}, "minPrice"),
    ({"minPrice": "NaN"}, "minPrice"),
    ({"minPrice": "Infinity"}, "minPrice"),
    ({"maxPrice": "-1"}, "maxPrice"),
    ({"minPrice": "500", "maxPrice": "100"}, "minPrice"),
    ({"sort": "cheapest"}, "sort"),
    ({"category": "nope"}, "category"),
    ({"brand": "oakline,nope"}, "brand"),
    ({"inStock": "maybe"}, "inStock"),
    ({"minRating": "0"}, "minRating"),
    ({"minRating": "6"}, "minRating"),
    ({"limit": "0"}, "limit"),
    ({"limit": "51"}, "limit"),
    ({"page": "0"}, "page"),
    ({"page": "abc"}, "page"),
    ({"page": "1" + "0" * 20}, "page"),
    ({"q": "a" * 101}, "q"),
])
def test_bad_input_is_a_400_never_a_500(client, params, field):
    assert_error(get(client, "/api/products", **params), 400, "VALIDATION_ERROR", field)


def test_all_invalid_parameters_are_reported_at_once(client):
    response = get(client, "/api/products", minPrice="abc", limit="0", sort="x")
    assert_error(response, 400, "VALIDATION_ERROR")
    details = response.json()["error"]["details"]
    assert {d["field"]: d["value"] for d in details} == {"minPrice": "abc", "limit": "0", "sort": "x"}


def test_other_endpoints_validate_and_404_in_the_same_shape(client):
    assert_error(get(client, "/api/products/shaggy-diamond-rug/reviews", sort="worst"), 400, "VALIDATION_ERROR", "sort")
    assert_error(get(client, "/api/collections/bestsellers", page="0"), 400, "VALIDATION_ERROR", "page")
    assert_error(get(client, "/api/products/no-such-product"), 404, "NOT_FOUND")
    assert_error(get(client, "/api/collections/no-such-collection"), 404, "NOT_FOUND")
    assert_error(get(client, "/api/no-such-endpoint"), 404, "NOT_FOUND")
    assert_error(client.post("/api/products"), 405, "METHOD_NOT_ALLOWED")


# ---------- the brief's own example ----------

def test_brief_example_request(client):
    body = get(client, "/api/products", q="candle", category="decor", inStock="true",
               sort="price_asc", page=1, limit=12).json()
    assert (body["page"], body["limit"], body["total"], body["totalPages"]) == (1, 12, 7, 1)
    assert body["items"][0] == {
        "id": "p043",
        "slug": "taper-candles-set-of-6",
        "name": "Taper Candles (Set of 6)",
        "brand": {"slug": "north-house", "name": "North House"},
        "category": {"slug": "candles", "name": "Candles"},
        "price": 12.99,
        "maxPrice": 12.99,
        "compareAtPrice": None,
        "inStock": True,
        "ratingAverage": 3.7,
        "reviewCount": 18,
        "image": {
            "url": f"{settings.PUBLIC_API_URL}/images/p043-1.jpg",
            "alt": "Taper Candles (Set of 6) - product photo",
        },
    }
    prices = [item["price"] for item in body["items"]]
    assert prices == sorted(prices)
    assert all(item["inStock"] for item in body["items"])


# ---------- business rules ----------

def test_r1_hidden_products_never_show_up(client, catalog):
    visible = {p["id"] for p in active(catalog)}
    hidden = [p for p in catalog["products"] if p["status"] != "active"]
    assert len(hidden) == 4

    items, total = fetch_all(client, "/api/products")
    assert {i["id"] for i in items} == visible and total == len(visible) == 116

    for product in hidden:
        for suffix in ("", "/reviews", "/similar"):
            assert_error(get(client, f"/api/products/{product['slug']}{suffix}"), 404, "NOT_FOUND")
        found, _ = fetch_all(client, "/api/products", q=product["name"])
        assert product["id"] not in {i["id"] for i in found}

    categories = get(client, "/api/categories").json()["items"]
    assert sum(c["productCount"] for c in categories) == len(visible)
    assert sum(b["productCount"] for b in get(client, "/api/brands").json()["items"]) == len(visible)
    for collection in get(client, "/api/collections").json()["items"]:
        found, total = fetch_all(client, f"/api/collections/{collection['slug']}")
        assert {i["id"] for i in found} <= visible and total == collection["productCount"]


def test_r2_list_price_is_the_lowest_variant_price(client, catalog):
    expected = {p["id"]: lowest_price(p) for p in active(catalog)}
    items, _ = fetch_all(client, "/api/products")
    assert {i["id"]: Decimal(str(i["price"])) for i in items} == expected

    # The rug's variants cost 349 / 559 / 839: price filters use 349 and are inclusive.
    assert "p001" in {i["id"] for i in fetch_all(client, "/api/products", minPrice=349, maxPrice=349)[0]}
    assert "p001" not in {i["id"] for i in fetch_all(client, "/api/products", maxPrice="348.99")[0]}
    assert "p001" not in {i["id"] for i in fetch_all(client, "/api/products", minPrice="349.01")[0]}

    in_range, _ = fetch_all(client, "/api/products", minPrice=100, maxPrice=300)
    assert {i["id"] for i in in_range} == {pid for pid, price in expected.items() if 100 <= price <= 300}


def test_r3_in_stock_means_any_variant_has_stock(client, catalog):
    expected = {p["id"] for p in active(catalog) if any(v["stock"] > 0 for v in p["variants"])}
    items, _ = fetch_all(client, "/api/products", inStock="true")
    assert {i["id"] for i in items} == expected
    assert len(expected) == 110  # the 6 fully sold-out products are left out

    every, _ = fetch_all(client, "/api/products")
    assert {i["id"] for i in every if i["inStock"]} == expected


def test_r4_only_live_collections_are_visible(client, catalog):
    now = timezone.now()

    def live(c):
        starts, ends = parse(c["startsAt"]), parse(c["endsAt"])
        return c["isActive"] and (starts is None or starts <= now) and (ends is None or now <= ends)

    expected = [c["slug"] for c in catalog["collections"] if live(c)]
    assert [c["slug"] for c in get(client, "/api/collections").json()["items"]] == expected

    # These stay hidden forever: one ended on 2026-08-31, one is inactive.
    for slug in ("summer-terrace", "calm-living"):
        assert slug not in expected
        assert_error(get(client, f"/api/collections/{slug}"), 404, "NOT_FOUND")

    status = {p["id"]: p["status"] for p in catalog["products"]}
    for c in catalog["collections"]:
        if live(c):
            in_order = [pid for pid in dict.fromkeys(c["productIds"]) if status[pid] == "active"]
            items, _ = fetch_all(client, f"/api/collections/{c['slug']}")
            assert [i["id"] for i in items] == in_order  # own order, no duplicates, no hidden products


def test_r5_old_price_only_when_above_the_price(client, catalog):
    for product in active(catalog):
        detail = get(client, f"/api/products/{product['slug']}").json()
        expected = {
            v["sku"]: (v["compareAtPrice"] if v["compareAtPrice"] is not None and v["compareAtPrice"] > v["price"] else None)
            for v in product["variants"]
        }
        assert {v["sku"]: v["compareAtPrice"] for v in detail["variants"]} == expected

    # P009-EMERAL-1 has compareAtPrice 34 below its price 39: no fake sale.
    p009 = get(client, "/api/products/" + next(p["slug"] for p in catalog["products"] if p["id"] == "p009")).json()
    assert next(v for v in p009["variants"] if v["sku"] == "P009-EMERAL-1")["compareAtPrice"] is None

    items, _ = fetch_all(client, "/api/products")
    assert all(i["compareAtPrice"] is None or i["compareAtPrice"] > i["price"] for i in items)


# ---------- sorting, paging, search ----------

@pytest.mark.parametrize("sort", SORTS)
def test_paging_returns_every_product_exactly_once_in_sort_order(client, catalog, sort):
    by_id = {p["id"]: p for p in active(catalog)}
    items, total = fetch_all(client, "/api/products", sort=sort)
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)) == total == len(by_id)

    key = {
        "price_asc": lambda p: lowest_price(p),
        "price_desc": lambda p: -lowest_price(p),
        "newest": lambda p: -parse(p["createdAt"]).timestamp(),
        "rating": lambda p: (p["ratingAverage"] is None, -(p["ratingAverage"] or 0)),  # unrated last
        "popular": lambda p: -p["salesCount"],
    }[sort]
    keys = [key(by_id[i]) for i in ids]
    assert keys == sorted(keys)


def haystack(catalog, p):
    """Everything `q` searches for one product, built straight from catalog.json."""
    brands = {b["id"]: b["name"] for b in catalog["brands"]}
    categories = {c["id"]: c for c in catalog["categories"]}
    category = categories[p["categoryId"]]
    parent = categories.get(category["parentId"]) if category["parentId"] else None
    fields = [p["name"], p["description"], brands[p["brandId"]], category["name"],
              parent["name"] if parent else "", p["attributes"].get("material") or "", *norm_tags(p["tags"])]
    return " ".join(fields).lower()


def matching(catalog, words):
    return {p["id"] for p in active(catalog) if all(w in haystack(catalog, p) for w in words)}


@pytest.mark.parametrize("q", ["handwov", "oak dining", "  OAK   Dining ", "wool rug", "candle", "lighting", "zzzz"])
def test_search_matches_all_words_partially_in_all_searched_fields(client, catalog, q):
    expected = matching(catalog, q.lower().split())
    items, _ = fetch_all(client, "/api/products", q=q)
    assert {i["id"] for i in items} == expected
    assert get(client, "/api/products", q=q).json()["correctedQuery"] is None
    if q == "zzzz":
        assert expected == set()
    else:
        assert expected  # the query means something in this data


# ---------- typo tolerance and autocomplete (bonus) ----------

@pytest.mark.parametrize("typo, meant", [
    ("candel", "candle"),
    ("lmap", "lamp"),
    ("oka", "oak"),
    ("jtue", "jute"),
    ("mirorr", "mirror"),
    ("CUHSION", "cushion"),
    ("oak tabel", "oak table"),
    ("velvt  cushon", "velvet cushion"),
    ("handwov rgu", "handwov rug"),
])
def test_typos_are_corrected_to_a_real_catalog_word(client, catalog, typo, meant):
    for word in typo.lower().split():
        if word not in meant.split():
            assert matching(catalog, [word]) == set()
    expected = matching(catalog, meant.split())
    assert expected

    items, total = fetch_all(client, "/api/products", q=typo)
    assert {i["id"] for i in items} == expected
    assert total == len(expected)
    assert get(client, "/api/products", q=typo).json()["correctedQuery"] == meant


@pytest.mark.parametrize("q", ["xyzq", "pilow", "qq", "zzzzzzzz"])
def test_words_with_no_close_match_stay_unmatched(client, q):
    body = get(client, "/api/products", q=q).json()
    assert body["total"] == 0 and body["items"] == []
    assert body["correctedQuery"] is None


def test_corrected_search_still_applies_filters_and_hides_hidden_products(client, catalog):
    hidden = {p["id"] for p in catalog["products"] if p["status"] != "active"}
    items, _ = fetch_all(client, "/api/products", q="candel", inStock="true", sort="price_asc")
    by_id = {p["id"]: p for p in catalog["products"]}
    expected = {i for i in matching(catalog, ["candle"]) if any(v["stock"] > 0 for v in by_id[i]["variants"])}
    assert {i["id"] for i in items} == expected
    assert not hidden & {i["id"] for i in items}
    prices = [i["price"] for i in items]
    assert prices == sorted(prices)


def test_edit_distance_counts_a_swap_as_one_edit():
    from catalog.api.search import closest_word, edit_distance

    assert edit_distance("candel", "candle", 2) == 1
    assert edit_distance("lmap", "lamp", 1) == 1
    assert edit_distance("wol", "wool", 1) == 1
    assert edit_distance("rug", "rug", 1) == 0
    assert edit_distance("kitten", "sitting", 3) == 3
    assert edit_distance("abc", "abcdefgh", 2) == 3
    words = [("candle", 8), ("candles", 3), ("can", 1)]
    assert closest_word("candel", words) == "candle"
    assert closest_word("candls", words) == "candle"
    assert closest_word("candlees", words) == "candles"
    assert closest_word("zzzzzz", words) is None


def suggest(client, q):
    response = get(client, "/api/search/suggest", q=q)
    assert response.status_code == 200
    return response.json()


def test_suggest_ranks_name_matches_first_and_only_shows_visible_products(client, catalog):
    body = suggest(client, "lamp")
    names = [p["name"].lower() for p in body["products"]]
    assert 0 < len(names) <= 6
    assert all("lamp" in n for n in names)
    visible = {p["slug"] for p in active(catalog)}
    assert all(p["slug"] in visible for p in body["products"])
    assert {"Floor Lamps", "Table Lamps"} <= {c["name"] for c in body["categories"]}
    assert body["correctedQuery"] is None

    oak = suggest(client, "oak")
    assert all(p["name"].lower().startswith("oak") for p in oak["products"][:3])
    assert [b["name"] for b in oak["brands"]] == ["Oakline"]


def test_suggest_never_shows_hidden_products(client, catalog):
    for product in catalog["products"]:
        if product["status"] != "active":
            body = suggest(client, product["name"])
            assert product["slug"] not in {p["slug"] for p in body["products"]}


def test_suggest_corrects_typos_and_skips_empty_groups(client, catalog):
    body = suggest(client, "candel")
    assert body["correctedQuery"] == "candle"
    assert body["products"] and all(p["id"] in matching(catalog, ["candle"]) for p in body["products"])
    assert [c["name"] for c in body["categories"]] == ["Candles"]

    glassware = suggest(client, "glassware")
    assert "Glassware" not in [c["name"] for c in glassware["categories"]]
    stone_hill = suggest(client, "stone hill")
    assert "Stone Hill" not in [b["name"] for b in stone_hill["brands"]]


@pytest.mark.parametrize("q", ["", "   "])
def test_suggest_with_no_words_returns_empty_groups(client, q):
    assert suggest(client, q) == {"products": [], "categories": [], "brands": [], "correctedQuery": None}


def test_suggest_rejects_overlong_input(client):
    assert_error(get(client, "/api/search/suggest", q="a" * 101), 400, "VALIDATION_ERROR", "q")


# ---------- detail, reviews, similar, counts ----------

def test_detail_matches_the_catalog(client, catalog):
    body = get(client, "/api/products/shaggy-diamond-rug").json()
    assert body["id"] == "p001"
    assert body["categoryPath"] == [{"slug": "home-textiles", "name": "Home Textiles"}, {"slug": "rugs", "name": "Rugs"}]
    assert body["brand"] == {"slug": "desert-weavers", "name": "Desert Weavers"}
    assert (body["price"], body["maxPrice"], body["inStock"]) == (349.0, 839.0, True)
    assert len(body["variants"]) == 5 and body["variants"][0]["sku"] == "P001-CREAM-1"

    # Missing and null attributes are the same: no product returns a null attribute.
    for product in active(catalog):
        attributes = get(client, f"/api/products/{product['slug']}").json()["attributes"]
        assert attributes == {k: v for k, v in product["attributes"].items() if v is not None}


def test_reviews_are_newest_first_and_complete(client, catalog):
    expected = sorted(
        (r for r in catalog["reviews"] if r["productId"] == "p001"),
        key=lambda r: r["createdAt"], reverse=True,
    )
    items, total = fetch_all(client, "/api/products/shaggy-diamond-rug/reviews")
    assert total == len(expected) == 18
    assert [i["createdAt"] for i in items] == [r["createdAt"] for r in expected]
    assert {i["id"] for i in items} == {r["id"] for r in expected}

    helpful, _ = fetch_all(client, "/api/products/shaggy-diamond-rug/reviews", sort="helpful")
    counts = [i["helpfulCount"] for i in helpful]
    assert counts == sorted(counts, reverse=True)


def test_similar_products_follow_the_scoring(client, catalog):
    products = {p["id"]: p for p in active(catalog)}
    categories = {c["id"]: c for c in catalog["categories"]}
    main = lambda p: categories[p["categoryId"]]["parentId"] or p["categoryId"]
    in_stock = lambda p: any(v["stock"] > 0 for v in p["variants"])

    def score(a, b):
        points = 3 * (a["categoryId"] == b["categoryId"]) + 2 * (main(a) == main(b)) + 2 * (a["brandId"] == b["brandId"])
        material = a["attributes"].get("material")
        points += 2 * bool(material and material == b["attributes"].get("material"))
        points += min(len(set(norm_tags(a["tags"])) & set(norm_tags(b["tags"]))), 3)
        low, high = lowest_price(a) * Decimal("0.7"), lowest_price(a) * Decimal("1.3")
        return points + (low <= lowest_price(b) <= high)

    for pid, product in products.items():
        ranked = sorted(
            (other for other in products.values() if other["id"] != pid and score(product, other) > 0),
            key=lambda o: (not in_stock(o), -score(product, o), -o["salesCount"], o["id"]),
        )
        got = [i["id"] for i in get(client, f"/api/products/{product['slug']}/similar").json()["items"]]
        assert got == [o["id"] for o in ranked[:4]], pid


def test_category_and_brand_counts(client, catalog):
    visible = active(catalog)
    tree = {c["slug"]: c for c in get(client, "/api/categories").json()["items"]}
    # Main categories in the shop's own order from catalog.json.
    assert list(tree) == [c["slug"] for c in catalog["categories"] if c["parentId"] is None]
    by_slug = {c["slug"]: c["id"] for c in catalog["categories"]}
    for slug, node in tree.items():
        assert node["productCount"] == sum(
            1 for p in visible
            if p["categoryId"] == by_slug[slug] or next(c for c in catalog["categories"] if c["id"] == p["categoryId"])["parentId"] == by_slug[slug]
        )
        for child in node["children"]:
            assert child["productCount"] == sum(1 for p in visible if p["categoryId"] == by_slug[child["slug"]])

    brand_ids = {b["slug"]: b["id"] for b in catalog["brands"]}
    for brand in get(client, "/api/brands").json()["items"]:
        assert brand["productCount"] == sum(1 for p in visible if p["brandId"] == brand_ids[brand["slug"]])
