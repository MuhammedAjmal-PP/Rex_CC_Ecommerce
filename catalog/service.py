from django.contrib import messages
from urllib.parse import urlparse, parse_qs
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ValidationError
from catalog.models import InventoryLog


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


@transaction.atomic
def update_stock(*, product_variant, change, reason, note, actor, reference_object):
    """
    Centralized stock update service.

    Args:
        product_variant (ProductVariant): Variant whose stock changes
        change (int): +ve for stock in, -ve for stock out
        reason (str): InventoryLog.REASON_CHOICES
        actor (User, optional): Who triggered the change
        reference_object (Model, optional): Order / OrderItem / Return
        note (str, optional): Extra context

    Returns:
        InventoryLog instance
    """

    if change == 0:
        raise ValidationError("Stock change cannot be Zero")

    before = product_variant.stock
    after = before + change

    if after < 0:
        raise ValidationError(
            "Insufficient stock"
        )  # change that into admin notification in future

    # update actual stock
    product_variant.stock = after
    product_variant.save(update_fields=["stock"])

    content_type = None
    object_id = None

    if reference_object:
        content_type = ContentType.objects.get_for_model(reference_object)
        object_id = reference_object.id

    # create inventory log
    log = InventoryLog.objects.create(
        product_variant=product_variant,
        change=change,
        stock_before=before,
        stock_after=after,
        reason=reason,
        note=note,
        actor=actor,
        content_type=content_type,
        object_id=object_id,
    )

    return log
