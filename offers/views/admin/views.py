from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from accounts.decorators import superuser_required
from django.contrib import messages

from offers.forms import OfferForm
from offers.models import Offer




@never_cache
@superuser_required
def offer_list(request):
    """Admin offer_list view with search, filtering, and pagination."""
    offers = Offer.objects.all().order_by("-created_at")

    search_query = request.GET.get("q", "").strip()
    if search_query:
        offers = offers.filter(
            Q(name__icontains=search_query)
            | Q(products__name__icontains=search_query)
            | Q(brands__name__icontains=search_query)
            | Q(categories__name__icontains=search_query)
        ).distinct()

    # ── Filter: offer type ───────────────────────
    offer_type = request.GET.get("offer_type", "").strip()
    if offer_type:
        offers = offers.filter(offer_type=offer_type)

    # ── Filter: status ───────────────────────────
    status_filter = request.GET.get("status", "").strip()
    now = timezone.now()
    if status_filter == "active":
        offers = offers.filter(is_active=True)
    elif status_filter == "inactive":
        offers = offers.filter(is_active=False)
    elif status_filter == "valid":
        offers = offers.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    elif status_filter == "expired":
        offers = offers.filter(end_date__lt=now)

    # ── Stats ────────────────────────────────────
    all_offers = Offer.objects.all()
    total_offers = all_offers.count()
    active_offers = all_offers.filter(is_active=True).count()
    inactive_offers = all_offers.filter(is_active=False).count()
    valid_offers = all_offers.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    ).count()
    expired_offers = all_offers.filter(end_date__lt=now).count()

    # ── Pagination ───────────────────────────────
    paginator = Paginator(offers, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "offers": page_obj,
        "search_query": search_query,
        "selected_type": offer_type,
        "status_filter": status_filter,
        "offer_type_choices": Offer.OFFER_TYPE_CHOICES,
        "total_offers": total_offers,
        "active_offers": active_offers,
        "inactive_offers": inactive_offers,
        "valid_offers": valid_offers,
        "expired_offers": expired_offers,
    }
    return render(request, "offers/admin/offer_list.html", context)


@never_cache
@superuser_required
def add_offer(request):
    """Create a new offer."""
    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer created successfully.")
            return redirect("admin_offers")
    else:
        form = OfferForm()
    return render(request, "offers/admin/offer_form.html", {"form": form})


@never_cache
@superuser_required
def edit_offer(request, pk):
    """Edit an existing offer."""
    offer = get_object_or_404(Offer, pk=pk)
    if request.method == "POST":
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer updated successfully.")
            return redirect("admin_offers")
    else:
        form = OfferForm(instance=offer)
    return render(
        request, "offers/admin/offer_form.html", {"form": form, "offer": offer}
    )


@never_cache
@superuser_required
def delete_offer(request, pk):
    """Delete an offer (POST-only)."""
    if request.method == "POST":
        offer = get_object_or_404(Offer, pk=pk)
        offer.delete()
        messages.success(request, "Offer deleted.")
    return redirect("admin_offers")
