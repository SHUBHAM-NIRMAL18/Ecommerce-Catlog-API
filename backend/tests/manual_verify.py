import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.test import Client

client = Client(SERVER_NAME="localhost")


def call(title, path, params=None):
    print("=" * 70)
    print(f">>> {title}")
    query = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
    print(f"HTTP GET {path}{query}")
    res = client.get(path, params or {})
    print(f"Status: {res.status_code}")
    print(json.dumps(res.json(), indent=2))
    print()


print("\n######################################################################")
print("  VERIFYING REST API ENDPOINTS & BUSINESS RULES R1 - R5")
print("######################################################################\n")

# R1: Only active products visible
call(
    "RULE R1: Active Product List (Total count 116, drafts/archived excluded)",
    "/api/products",
    {"limit": 2},
)
call(
    "RULE R1: Draft Product p023 'Extendable Dining Table' Returns 404",
    "/api/products/extendable-dining-table",
)
call(
    "RULE R1: Archived Product p080 'Bamboo Pendant Light' Returns 404",
    "/api/products/bamboo-pendant-light",
)

# R2: Lowest variant price
call(
    "RULE R2: Shaggy Diamond Rug variants are 349, 559, 839 -> list price is 349.0",
    "/api/products/shaggy-diamond-rug",
)
call(
    "RULE R2: Filter by Price Range [100, 150] matches lowest variant price",
    "/api/products",
    {"minPrice": "100", "maxPrice": "150", "limit": 2},
)

# R3: In-stock definition
call(
    "RULE R3: In-Stock Only filter (inStock=true) returns 110 of 116 active products",
    "/api/products",
    {"inStock": "true", "limit": 2},
)
call(
    "RULE R3: Completely Sold Out Product p013 has inStock=False",
    "/api/products/soft-wool-blanket",
)

# R4: Live Collections
call(
    "RULE R4: Live Collections List (Only 6 live collections returned today)",
    "/api/collections",
)
call(
    "RULE R4: Expired Collection 'summer-terrace' (ended Aug 2026) Returns 404",
    "/api/collections/summer-terrace",
)
call(
    "RULE R4: Inactive Collection 'calm-living' (isActive=False) Returns 404",
    "/api/collections/calm-living",
)

# R5: Compare-at Sale Price
call(
    "RULE R5: Product p009 Velvet Cushion (P009-MUSTAR-1 has valid sale 39 < 50.9; P009-EMERAL-1 34 < 39 is null)",
    "/api/products/velvet-cushion",
)

# Brief example query
call(
    "BRIEF EXAMPLE: Multi-word search, category filter, inStock, sort=price_asc",
    "/api/products",
    {
        "q": "candle",
        "category": "decor",
        "inStock": "true",
        "sort": "price_asc",
        "page": 1,
        "limit": 2,
    },
)

# Similar products
call(
    "SIMILAR PRODUCTS: Top 4 similar items for 'Shaggy Diamond Rug'",
    "/api/products/shaggy-diamond-rug/similar",
)

# Unified Error
call(
    "UNIFIED ERROR SHAPE: Validation Error (400 Bad Request)",
    "/api/products",
    {"minPrice": "abc", "maxPrice": "50"},
)

