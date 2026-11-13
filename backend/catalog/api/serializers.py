"""Input validation for query parameters, and the JSON shape of every response (camelCase)."""

from django.conf import settings
from rest_framework import serializers

from catalog.models import Brand, Category

from .pagination import PageQuerySerializer

SORTS = ["price_asc", "price_desc", "newest", "rating", "popular"]


def image_url(path):
    """Absolute URL the browser can load, e.g. http://localhost:8000/images/p001-1.jpg."""
    return f"{settings.PUBLIC_API_URL}/{path.lstrip('/')}"


def sale_price(price, compare_at_price):
    """R5: only show an old price when it is really above the price."""
    if price is not None and compare_at_price is not None and compare_at_price > price:
        return compare_at_price
    return None


# ---------- Input ----------

class ProductQuerySerializer(PageQuerySerializer):
    """Validates GET /api/products query parameters. Every problem becomes a 400."""

    q = serializers.CharField(required=False, allow_blank=True, max_length=100)
    category = serializers.CharField(required=False)
    brand = serializers.CharField(required=False)
    minPrice = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    maxPrice = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    inStock = serializers.BooleanField(required=False, default=False)
    minRating = serializers.DecimalField(max_digits=2, decimal_places=1, min_value=1, max_value=5, required=False)
    sort = serializers.ChoiceField(choices=SORTS, default="newest")

    def validate_q(self, value):
        """Lowercase words; extra spaces are ignored. Empty q means no search."""
        return value.lower().split()

    def validate_category(self, value):
        category = Category.objects.filter(slug=value.strip()).first()
        if category is None:
            raise serializers.ValidationError(f"Unknown category '{value}'.")
        return category

    def validate_brand(self, value):
        slugs = list(dict.fromkeys(s.strip() for s in value.split(",") if s.strip()))
        brands = list(Brand.objects.filter(slug__in=slugs))
        unknown = sorted(set(slugs) - {b.slug for b in brands})
        if unknown:
            raise serializers.ValidationError(f"Unknown brand(s): {', '.join(unknown)}.")
        return brands

    def validate(self, data):
        low, high = data.get("minPrice"), data.get("maxPrice")
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"minPrice": "minPrice must not be greater than maxPrice."})
        return data


class ReviewQuerySerializer(PageQuerySerializer):
    """GET /api/products/:slug/reviews. `helpful` is the bonus sort by helpfulCount."""

    sort = serializers.ChoiceField(choices=["newest", "helpful"], default="newest")


# ---------- Output ----------

class BrandRefSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()


class CategoryRefSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()


class ImageSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()
    alt = serializers.CharField()

    def get_url(self, image):
        return image_url(image.url)


class ProductListSerializer(serializers.Serializer):
    """A product card. Expects a queryset from views.visible_products()."""

    id = serializers.CharField(source="source_id")
    slug = serializers.CharField()
    name = serializers.CharField()
    brand = BrandRefSerializer()
    category = CategoryRefSerializer()
    price = serializers.DecimalField(source="min_price", max_digits=10, decimal_places=2)
    maxPrice = serializers.DecimalField(source="max_price", max_digits=10, decimal_places=2)
    compareAtPrice = serializers.SerializerMethodField()
    inStock = serializers.BooleanField(source="in_stock")
    ratingAverage = serializers.DecimalField(source="rating_average", max_digits=2, decimal_places=1)
    reviewCount = serializers.IntegerField(source="review_count")
    image = serializers.SerializerMethodField()

    def get_compareAtPrice(self, product):
        return sale_price(product.min_price, product.list_compare_at_price)

    def get_image(self, product):
        first = next(iter(product.images.all()), None)  # prefetched, ordered by position
        return ImageSerializer(first).data if first else None


class VariantSerializer(serializers.Serializer):
    sku = serializers.CharField()
    color = serializers.CharField()
    size = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    compareAtPrice = serializers.SerializerMethodField()
    stock = serializers.IntegerField()

    def get_compareAtPrice(self, variant):
        return sale_price(variant.price, variant.compare_at_price)


class ProductDetailSerializer(ProductListSerializer):
    """Everything on the product page. Adds to the card fields; `image` is replaced by `images`."""

    image = None
    category = None
    description = serializers.CharField()
    categoryPath = serializers.SerializerMethodField()
    attributes = serializers.JSONField()  # null values were dropped by the seed
    features = serializers.ListField(child=serializers.CharField())
    tags = serializers.ListField(child=serializers.CharField())
    images = ImageSerializer(many=True)
    variants = VariantSerializer(many=True)

    def get_categoryPath(self, product):
        """Main category first, then the sub-category: [Home Textiles, Rugs]."""
        path, category = [], product.category
        while category is not None:
            path.insert(0, {"slug": category.slug, "name": category.name})
            category = category.parent
        return path


class BrandSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    country = serializers.CharField()
    productCount = serializers.IntegerField(source="product_count")


class CollectionSerializer(serializers.Serializer):
    id = serializers.CharField(source="source_id")
    slug = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    startsAt = serializers.DateTimeField(source="starts_at")
    endsAt = serializers.DateTimeField(source="ends_at")
    productCount = serializers.IntegerField(source="product_count")


class ReviewSerializer(serializers.Serializer):
    id = serializers.CharField(source="source_id")
    rating = serializers.IntegerField()
    title = serializers.CharField()
    body = serializers.CharField(allow_null=True)
    verifiedPurchase = serializers.BooleanField(source="verified_purchase")
    helpfulCount = serializers.IntegerField(source="helpful_count")
    createdAt = serializers.DateTimeField(source="created_at")
