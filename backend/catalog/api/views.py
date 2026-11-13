from django.db import connection
from django.db.models import F, OuterRef, Prefetch, Q, Subquery
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalog.models import Product, ProductImage, ProductVariant

from .pagination import page_response, paginate
from .serializers import ProductListSerializer, ProductQuerySerializer

# Every sort ends with id, so products with the same value keep a fixed order
# and paging never shows a product twice or skips one.
SORT_ORDER = {
    "price_asc": [F("min_price").asc(nulls_last=True), "id"],
    "price_desc": [F("min_price").desc(nulls_last=True), "id"],
    "newest": ["-created_at", "id"],
    "rating": [F("rating_average").desc(nulls_last=True), "id"],  # unrated last
    "popular": ["-sales_count", "id"],
}


def visible_products():
    """R1: the starting point for every product query. Only active products, ever."""
    return Product.objects.filter(status=Product.Status.ACTIVE)


def with_card_data(queryset):
    """Adds what a product card needs, without N+1 queries."""
    variants = ProductVariant.objects.filter(product=OuterRef("pk"))
    return queryset.select_related("brand", "category").annotate(
        # Old price of the cheapest variant, the one the list price comes from (R2, R5).
        list_compare_at_price=Subquery(variants.order_by("price", "id").values("compare_at_price")[:1]),
        # Highest variant price, so the UI can show "from €X" only when prices differ.
        max_price=Subquery(variants.order_by("-price").values("price")[:1]),
    ).prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("position")))


def filter_products(queryset, params):
    """Applies the validated filters. Everything runs in the database query."""
    for word in params.get("q") or []:
        # search_text is stored lowercase, so `contains` (not icontains) can use the trigram index.
        queryset = queryset.filter(search_text__contains=word)

    category = params.get("category")
    if category is not None:
        # A main category includes all of its sub-categories.
        queryset = queryset.filter(Q(category=category) | Q(category__parent=category))

    if params.get("brand"):
        queryset = queryset.filter(brand__in=params["brand"])
    if params.get("minPrice") is not None:
        queryset = queryset.filter(min_price__gte=params["minPrice"])
    if params.get("maxPrice") is not None:
        queryset = queryset.filter(min_price__lte=params["maxPrice"])
    if params.get("inStock"):
        queryset = queryset.filter(in_stock=True)  # R3
    if params.get("minRating") is not None:
        queryset = queryset.filter(rating_average__gte=params["minRating"])  # unrated never match

    return queryset.order_by(*SORT_ORDER[params["sort"]])


@api_view(["GET"])
def product_list(request):
    params = ProductQuerySerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    p = params.validated_data

    products = filter_products(with_card_data(visible_products()), p)
    rows, meta = paginate(products, p["page"], p["limit"])
    return Response(page_response(ProductListSerializer(rows, many=True).data, meta))


@api_view(["GET"])
def health(request):
    """Liveness check for Docker: the API is up and the database answers."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Response({"status": "ok"})
