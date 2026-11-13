from decimal import Decimal

from django.db import connection
from django.db.models import Case, Count, F, IntegerField, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.expressions import RawSQL
from django.db.models.functions import Least
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from catalog.models import Brand, Category, Collection, Product, ProductImage, ProductVariant

from .pagination import PageQuerySerializer, page_response, paginate
from .serializers import (
    BrandSerializer,
    CollectionSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductQuerySerializer,
    ReviewQuerySerializer,
    ReviewSerializer,
)

# Every sort ends with id, so products with the same value keep a fixed order
# and paging never shows a product twice or skips one.
SORT_ORDER = {
    "price_asc": [F("min_price").asc(nulls_last=True), "id"],
    "price_desc": [F("min_price").desc(nulls_last=True), "id"],
    "newest": ["-created_at", "id"],
    "rating": [F("rating_average").desc(nulls_last=True), "id"],  # unrated last
    "popular": ["-sales_count", "id"],
}

REVIEW_ORDER = {
    "newest": ["-created_at", "id"],
    "helpful": ["-helpful_count", "-created_at", "id"],
}

# Similar products: points for what a candidate has in common with the product.
SIMILARITY_WEIGHTS = {
    "same_subcategory": 3,
    "same_main_category": 2,
    "same_brand": 2,
    "same_material": 2,
    "shared_tag": 1,  # per shared tag, at most MAX_SHARED_TAGS
    "similar_price": 1,  # lowest price within ±30%
}
MAX_SHARED_TAGS = 3
SIMILAR_PRICE_RANGE = Decimal("0.30")
SIMILAR_LIMIT = 4


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


def get_visible_product(slug, queryset=None):
    """The product with this slug, or a 404 if it doesn't exist or is hidden (R1)."""
    product = (queryset if queryset is not None else visible_products()).filter(slug=slug).first()
    if product is None:
        raise NotFound(f"Product '{slug}' not found.")
    return product


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


def similar_products(product):
    """Top 4 visible products by similarity score, computed in one SQL query.

    Never the product itself, no duplicates (one row per product), only visible
    products (R1), only products with a score above 0, and sold-out products last.
    """
    w = SIMILARITY_WEIGHTS
    main_category_id = product.category.parent_id or product.category_id

    def points(condition, weight):
        return Case(When(condition, then=Value(weight)), default=Value(0), output_field=IntegerField())

    score = (
        points(Q(category_id=product.category_id), w["same_subcategory"])
        + points(Q(category__parent_id=main_category_id) | Q(category_id=main_category_id), w["same_main_category"])
        + points(Q(brand_id=product.brand_id), w["same_brand"])
    )

    material = product.attributes.get("material")
    if material:
        score += points(Q(attributes__material=material), w["same_material"])

    if product.tags:
        # Number of tags both products have; the tag list is passed as a query parameter, never glued in.
        shared_tags = RawSQL(
            "cardinality(ARRAY(SELECT unnest(product.tags) INTERSECT SELECT unnest(%s::varchar[])))",
            (list(product.tags),),
            output_field=IntegerField(),
        )
        score += Least(shared_tags, Value(MAX_SHARED_TAGS)) * Value(w["shared_tag"])

    if product.min_price is not None:
        low = product.min_price * (1 - SIMILAR_PRICE_RANGE)
        high = product.min_price * (1 + SIMILAR_PRICE_RANGE)
        score += points(Q(min_price__range=(low, high)), w["similar_price"])

    return (
        with_card_data(visible_products().exclude(pk=product.pk))
        .annotate(similarity=score)
        .filter(similarity__gt=0)
        .order_by("-in_stock", "-similarity", "-sales_count", "id")[:SIMILAR_LIMIT]
    )


@api_view(["GET"])
def product_list(request):
    params = ProductQuerySerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    p = params.validated_data

    products = filter_products(with_card_data(visible_products()), p)
    rows, meta = paginate(products, p["page"], p["limit"])
    return Response(page_response(ProductListSerializer(rows, many=True).data, meta))


@api_view(["GET"])
def product_detail(request, slug):
    queryset = with_card_data(visible_products()).select_related("category__parent").prefetch_related(
        Prefetch("variants", queryset=ProductVariant.objects.order_by("id"))
    )
    product = get_visible_product(slug, queryset)
    return Response(ProductDetailSerializer(product).data)


@api_view(["GET"])
def product_reviews(request, slug):
    params = ReviewQuerySerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    p = params.validated_data

    product = get_visible_product(slug)
    reviews = product.reviews.order_by(*REVIEW_ORDER[p["sort"]])
    rows, meta = paginate(reviews, p["page"], p["limit"])
    return Response(page_response(ReviewSerializer(rows, many=True).data, meta))


@api_view(["GET"])
def product_similar(request, slug):
    product = get_visible_product(slug, visible_products().select_related("category"))
    return Response({"items": ProductListSerializer(similar_products(product), many=True).data})


ACTIVE = Product.Status.ACTIVE


@api_view(["GET"])
def category_list(request):
    """Category tree. Counts only visible products (R1); a main category's count includes its subs."""
    categories = list(
        Category.objects.annotate(
            direct_count=Count("products", filter=Q(products__status=ACTIVE))
        ).order_by("id")  # the shop's own order from catalog.json
    )

    def node(category):
        return {"slug": category.slug, "name": category.name, "productCount": category.direct_count, "children": []}

    nodes = {c.id: node(c) for c in categories}
    tree = []
    for category in categories:
        if category.parent_id is None:
            tree.append(nodes[category.id])
        else:
            parent = nodes[category.parent_id]
            parent["children"].append(nodes[category.id])
            parent["productCount"] += category.direct_count
    return Response({"items": tree})


@api_view(["GET"])
def brand_list(request):
    brands = Brand.objects.annotate(
        product_count=Count("products", filter=Q(products__status=ACTIVE))
    ).order_by("name", "id")
    return Response({"items": BrandSerializer(brands, many=True).data})


def visible_collections():
    """R4: active and inside its date window today. productCount counts visible products only (R1)."""
    return Collection.objects.live().annotate(
        product_count=Count("items", filter=Q(items__product__status=ACTIVE))
    )


@api_view(["GET"])
def collection_list(request):
    collections = visible_collections().order_by("id")
    return Response({"items": CollectionSerializer(collections, many=True).data})


@api_view(["GET"])
def collection_detail(request, slug):
    params = PageQuerySerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    p = params.validated_data

    collection = visible_collections().filter(slug=slug).first()
    if collection is None:
        raise NotFound(f"Collection '{slug}' not found.")

    # The collection's own order (position); hidden products are left out (R1).
    products = with_card_data(
        visible_products().filter(collection_items__collection=collection)
    ).order_by("collection_items__position", "id")
    rows, meta = paginate(products, p["page"], p["limit"])
    return Response({
        "collection": CollectionSerializer(collection).data,
        **page_response(ProductListSerializer(rows, many=True).data, meta),
    })


@api_view(["GET"])
def health(request):
    """Liveness check for Docker: the API is up and the database answers."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Response({"status": "ok"})
