from django.contrib import admin
from .models import Address, BlockedEmail


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'city', 'state', 'address_type', 'is_default', 'created_at']
    list_filter = ['address_type', 'is_default', 'state']
    search_fields = ['full_name', 'user__email', 'city', 'postal_code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BlockedEmail)
class BlockedEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'original_user', 'blocked_at', 'reason']
    list_filter = ['blocked_at']
    search_fields = ['email', 'original_user__email']
    readonly_fields = ['blocked_at']
