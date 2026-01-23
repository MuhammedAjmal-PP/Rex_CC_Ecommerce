from email import message
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from customers.user_profile.forms import AddressForm
from customers.user_profile.models import Address


@never_cache
@login_required
def address_list(request):
    """list addresses of user"""

    addresses = Address.active.filter(user=request.user)

    context = {
        "addresses": addresses,
    }

    return render(request, "user_profile/address.html", context)


@never_cache
@login_required
def add_address(request):
    """add addresses"""
    if (
        Address.active.filter(user=request.user).count()
        >= settings.MAX_ADDRESSES_PER_USER
    ):
        messages.error(
            request,
            f"You can only save up to {settings.MAX_ADDRESSES_PER_USER} addresses.",
        )
        return redirect("user_address")

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully")
            return redirect("user_address")
    else:
        form = AddressForm()
    return render(request, "user_profile/address_form.html", {"form": form})


@never_cache
@login_required
def edit_address(request, address_id):
    """Edit an existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address updated successfully")
            return redirect("user_address")

    else:
        form = AddressForm(instance=address)

    return render(request, "user_profile/address_form.html", {"form": form})


@login_required
@require_POST
def delete_address(request, address_id):
    """Delete a address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    address.is_active = False
    address.save()

    if address.is_default:
        next_address = (
            Address.active.filter(user=request.user).order_by("-created_at").first()
        )
        if next_address:
            next_address.is_default = True
            next_address.save()

    return JsonResponse(
        {
            "success": True,
            "message": "Address deleted successfully!",
        }
    )


@login_required
@require_POST
def toggle_default_address(request, address_id):
    """Set an address as default"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    return JsonResponse(
        {
            "success": True,
            "message": "Default address updated!",
        }
    )
