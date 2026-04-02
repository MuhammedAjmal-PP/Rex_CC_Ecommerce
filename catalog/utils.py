"""
Variant display utility — the ONE place to prepare variants for templates.

Usage:
    from catalog.utils import pack_variants, get_offer_variants

    # In any view that displays variant cards:
    variants = ProductVariant.objects.filter(...)
        .select_related("product", "product__brand")
        .prefetch_related("images")

    packed = pack_variants(variants)
    # Each variant now has: .primary_image, .discount_percentage,
    #                        .discount_amount, .final_price

    # For "top discounted" section:
    offer_variants = get_offer_variants(base_queryset, limit=8)
"""

from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from catalog.models import Product
from offers.models import Offer

# ─── INTERNAL HELPERS ───────────────────────────────────────


def _load_offer_data():
    """
    Load all active offers and build lookup sets.
    Returns a list of (discount, product_ids, category_ids, brand_ids).
    Cost: 1 DB query (+ prefetch).
    """
    now = timezone.now()
    active_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
    ).prefetch_related("products", "categories", "brands")

    offer_data = []
    for offer in active_offers:
        d = int(offer.discount_value)
        pids = set(offer.products.values_list("id", flat=True))
        cids = set(offer.categories.values_list("id", flat=True))
        bids = set(offer.brands.values_list("id", flat=True))
        offer_data.append((d, pids, cids, bids))

    return offer_data


def _load_category_map(product_ids):
    """
    Build {product_id: {cat_id, ...}} from the M2M through table.
    Cost: 1 DB query.
    """
    category_map = {}
    if product_ids:
        rows = Product.category.through.objects.filter(
            product_id__in=product_ids
        ).values_list("product_id", "category_id")
        for pid, cid in rows:
            category_map.setdefault(pid, set()).add(cid)
    return category_map


def _best_discount(variant, offer_data, category_map):
    """
    Compute the best discount % for a single variant.
    Pure Python — zero DB queries.
    """
    cat_ids = category_map.get(variant.product_id, set())
    best = variant.discount_rate

    for d, pids, cids, bids in offer_data:
        if (
            variant.product_id in pids
            or cat_ids & cids
            or variant.product.brand_id in bids
        ):
            best = max(best, d)

    return best


# ─── PUBLIC API ─────────────────────────────────────────────


def pack_variants(variants, offer_data=None):
    """
    Enrich each variant with computed display fields.
    Accepts optional pre-loaded offer_data to avoid a second DB hit.
    Cost: 1 query (_load_offer_data) + 1 query (_load_category_map).
    If offer_data is provided, skips the first query.

    Specifically, it attaches:
        variant.primary_image        → ProductImage or None
        variant.discount_percentage  → int (0–100)
        variant.discount_amount      → Decimal
        variant.final_price          → Decimal

    Callers should apply:
        .select_related("product", "product__brand")
        .prefetch_related("images")
    """
    variants_list = list(variants)
    if not variants_list:
        return variants_list
    if offer_data is None:
        offer_data = _load_offer_data()
    product_ids = {v.product_id for v in variants_list}
    category_map = _load_category_map(product_ids)

    for variant in variants_list:

        # ── Primary image (from prefetch cache) ──
        primary_image = None
        for img in variant.images.all():
            if img.is_primary:
                primary_image = img
                break
        variant.primary_image = primary_image

        # ── Discount ──
        pct = _best_discount(variant, offer_data, category_map)
        variant.discount_percentage = pct

        if pct > 0:
            variant.discount_amount = variant.price * Decimal(pct) / Decimal(100)
        else:
            variant.discount_amount = Decimal("0.00")

        variant.final_price = variant.price - variant.discount_amount

    return variants_list


def get_offer_variants(variant_queryset, *, limit=8):
    """
    Return the top `limit` variants sorted by highest discount.

    1. Loads active offers
    2. Filters the queryset to variants that *could* have a discount
    3. Packs them with pack_variants()
    4. Sorts by discount descending

    DB cost: ~4 queries (offers twice + category + filtered variants).
    """
    # Fix #17: load offer data once and pass into pack_variants
    offer_data = _load_offer_data()

    # Collect IDs that have offers
    offer_product_ids = set()
    offer_category_ids = set()
    offer_brand_ids = set()

    for _, pids, cids, bids in offer_data:
        offer_product_ids |= pids
        offer_category_ids |= cids
        offer_brand_ids |= bids

    # Filter to variants that might have a discount
    candidates = (
        variant_queryset.filter(
            Q(discount_rate__gt=0)
            | Q(product_id__in=offer_product_ids)
            | Q(product__category__id__in=offer_category_ids)
            | Q(product__brand_id__in=offer_brand_ids)
        )
        .select_related("product", "product__brand")
        .prefetch_related("images")
        .distinct()
    )

    packed = pack_variants(candidates, offer_data=offer_data)

    # Sort by discount and slice
    packed.sort(key=lambda v: v.discount_percentage, reverse=True)
    return packed[:limit]
