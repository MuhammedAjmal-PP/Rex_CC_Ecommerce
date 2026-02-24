from django.db.models import Q
from django.utils import timezone

from offers.models import Offer


def get_offer_variants(variant_queryset, *, limit=8):
    """
    Return the top `limit` variants sorted by highest effective discount.

    Computes all offer lookups in a single pass (no per-variant queries)
    and injects `_cached_discount_percentage` on each returned variant so
    downstream code (templates, properties) can reuse it for free.

    Args:
        variant_queryset: A base ProductVariant queryset (already filtered
                          for active/published products).
        limit:            Max number of variants to return.

    Returns:
        A list of ProductVariant instances, sorted by discount descending.
    """

    now = timezone.now()
    active_offers = Offer.objects.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    ).prefetch_related("products", "categories", "brands")

    # Build per-offer lookup data in ONE pass — zero per-variant queries
    offer_data = []
    offer_product_ids = set()
    offer_category_ids = set()
    offer_brand_ids = set()

    for offer in active_offers:
        d = int(offer.discount_value)
        pids = set(offer.products.values_list("id", flat=True))
        cids = set(offer.categories.values_list("id", flat=True))
        bids = set(offer.brands.values_list("id", flat=True))
        offer_data.append((d, pids, cids, bids))
        offer_product_ids |= pids
        offer_category_ids |= cids
        offer_brand_ids |= bids

    offer_variants = variant_queryset.filter(
        Q(discount_rate__gt=0)
        | Q(product_id__in=offer_product_ids)
        | Q(product__category__id__in=offer_category_ids)
        | Q(product__brand_id__in=offer_brand_ids)
    ).prefetch_related("product__category").distinct()

    offer_variants = list(offer_variants)

    # Compute discount in Python — no extra queries
    for v in offer_variants:
        cat_ids = set(v.product.category.values_list("id", flat=True))
        best = v.discount_rate
        for d, pids, cids, bids in offer_data:
            if v.product_id in pids or cat_ids & cids or v.product.brand_id in bids:
                best = max(best, d)
        v._cached_discount_percentage = best

    offer_variants.sort(key=lambda v: v._cached_discount_percentage, reverse=True)
    return offer_variants[:limit]
