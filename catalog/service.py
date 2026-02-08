from django.contrib import messages
from urllib.parse import urlparse, parse_qs


def manage_product_draft_status(request, product):
    """
    When a ProductVariant is deleted or is drafted,
    check if the parent Product has any remaining variants.
    If not, set is_drafted = True.

    """

    # We only care about variants that are NOT deleted and NOT drafted
    active_variants_exist = product.variants.filter(
        is_deleted=False, is_drafted=False
    ).exists()

    if not active_variants_exist:
        if not product.is_drafted:
            product.is_drafted = True
            product.save(update_fields=["is_drafted"])
            messages.warning(
                request,
                f"The product '{product.name}' has been auto-drafted because it has no active variants.",
            )


def get_category_from_referer(request):
    referer = request.META.get("HTTP_REFERER")

    if not referer:
        return None

    parsed_url = urlparse(referer)
    query_params = parse_qs(parsed_url.query)

    category_slug = query_params.get("category")

    if not category_slug:
        return None

    return category_slug[0]
