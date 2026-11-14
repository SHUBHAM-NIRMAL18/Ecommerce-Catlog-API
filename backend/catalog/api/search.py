"""Search helpers: typo correction for `q`, and the queries behind autocomplete.

A search word that matches nothing is swapped for the closest real word from the
catalog (edit distance, a swap of two neighbour letters counts as one edit). Words
that already match are never changed, so correct searches behave exactly as before.
"""

from django.db import connection
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.functions import Lower

from catalog.models import Brand, Category, Product

MIN_WORD_LENGTH = 3
SUGGEST_PRODUCTS = 6
SUGGEST_GROUPS = 3

VOCABULARY_SQL = """
    SELECT word, COUNT(DISTINCT product.id)
    FROM product, unnest(regexp_split_to_array(product.search_text, '[^[:alnum:]]+')) AS word
    WHERE product.status = %s AND length(word) >= %s
    GROUP BY word
"""


def max_edits(word):
    return 1 if len(word) <= 5 else 2


def edit_distance(a, b, limit):
    """Optimal string alignment distance, or limit + 1 as soon as it is clearly larger."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous2, previous = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        current = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                current[j] = min(current[j], previous2[j - 2] + 1)
        if min(current) > limit:
            return limit + 1
        previous2, previous = previous, current
    return previous[-1]


def vocabulary():
    """Every word in visible products' search text, with how many products use it."""
    with connection.cursor() as cursor:
        cursor.execute(VOCABULARY_SQL, [Product.Status.ACTIVE, MIN_WORD_LENGTH])
        return cursor.fetchall()


def closest_word(word, words):
    """Fewest edits wins; on a tie, the word more products use, then alphabetical."""
    limit = max_edits(word)
    best = None
    for candidate, uses in words:
        distance = edit_distance(word, candidate, limit)
        if distance <= limit:
            key = (distance, -uses, candidate)
            if best is None or key < best:
                best = key
    return best[2] if best else None


def correct_terms(terms):
    """Returns (terms to search with, corrected query or None when nothing changed)."""
    visible = Product.objects.filter(status=Product.Status.ACTIVE)
    corrected, words = [], None
    for term in terms:
        if len(term) < MIN_WORD_LENGTH or visible.filter(search_text__contains=term).exists():
            corrected.append(term)
            continue
        if words is None:
            words = vocabulary()
        corrected.append(closest_word(term, words) or term)
    if corrected == list(terms):
        return list(terms), None
    return corrected, " ".join(corrected)


def match_terms(queryset, terms):
    """Every word must appear somewhere in search_text (stored lowercase, so the trigram index is used)."""
    for term in terms:
        queryset = queryset.filter(search_text__contains=term)
    return queryset


def name_rank(terms):
    """0 when the name starts with the query, 1 when it holds every word, 2 otherwise."""
    phrase = " ".join(terms)
    all_in_name = Q()
    for term in terms:
        all_in_name &= Q(lower_name__contains=term)
    return Case(
        When(lower_name__startswith=phrase, then=Value(0)),
        When(all_in_name, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )


def suggest_products(queryset, terms):
    return (
        match_terms(queryset, terms)
        .annotate(lower_name=Lower("name"))
        .annotate(rank=name_rank(terms))
        .order_by("rank", "-sales_count", "id")[:SUGGEST_PRODUCTS]
    )


def names_matching(model, terms, has_products):
    """Categories or brands whose name holds every word and that have visible products."""
    queryset = model.objects.annotate(lower_name=Lower("name")).filter(has_products).distinct()
    for term in terms:
        queryset = queryset.filter(lower_name__contains=term)
    return queryset.order_by("name", "id")[:SUGGEST_GROUPS]


def suggest_categories(terms):
    active = Q(products__status=Product.Status.ACTIVE) | Q(children__products__status=Product.Status.ACTIVE)
    return names_matching(Category, terms, active)


def suggest_brands(terms):
    return names_matching(Brand, terms, Q(products__status=Product.Status.ACTIVE))
