from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..models import Address
from ..forms import AddressForm


@login_required
def address_list(request):
    """Display all user addresses"""
    addresses = Address.objects.filter(user=request.user)
    return render(request, "user_profile/addresses.html", {"addresses": addresses})


@login_required
def address_add(request):
    """Add a new address"""
    
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully!")
            return redirect("address_list")
    else:
        form = AddressForm()
    
    addresses = Address.objects.filter(user=request.user)
    return render(request, "user_profile/addresses.html", {
        "addresses": addresses,
        "form": form,
        "show_add_modal": True
    })


@login_required
def address_edit(request, address_id):
    """Edit an existing address"""
    
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect("address_list")
    else:
        form = AddressForm(instance=address)
    
    addresses = Address.objects.filter(user=request.user)
    return render(request, "user_profile/addresses.html", {
        "addresses": addresses,
        "form": form,
        "edit_address": address,
        "show_edit_modal": True
    })


@login_required
def address_delete(request, address_id):
    """Delete an address"""
    
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted successfully!")
        return redirect("address_list")
    
    addresses = Address.objects.filter(user=request.user)
    return render(request, "user_profile/addresses.html", {
        "addresses": addresses,
        "delete_address": address,
        "show_delete_modal": True
    })


@login_required
def address_set_default(request, address_id):
    """Set an address as default"""
    
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()  # The model's save method handles unsetting other defaults
    
    messages.success(request, "Default address updated!")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True})
    
    return redirect("address_list")
