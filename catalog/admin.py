from django.contrib import admin
from .models import Brand, Category, Product, ProductImage, ProductVariant
from django.contrib import messages

# Register your models here.


# admin.site.register(Brand)
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    actions = ["activate_brands", "deactivate_brands"]

    @admin.action(description="Activate selected brands")
    def activate_brands(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} brand(s) activated successfully.",
            messages.SUCCESS,
        )

    @admin.action(description="Deactivate selected brands")
    def deactivate_brands(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} brand(s) deactivated successfully.",
            messages.WARNING,
        )


# admin.site.register(Category)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    actions = ["activate_categories", "deactivate_categories"]

    @admin.action(description="Activate selected categories")
    def activate_categories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} category(s) activated successfully.",
            messages.SUCCESS,
        )

    @admin.action(description="Deactivate selected categories")
    def deactivate_categories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} category(s) deactivated successfully.",
            messages.WARNING,
        )


# admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_drafted",
        "brand",
    )
    list_filter = ("is_drafted",)
    actions = ["draft_products", "publish_products"]

    @admin.action(description="Move selected products to draft")
    def draft_products(self, request, queryset):
        updated = queryset.update(is_drafted=True)
        self.message_user(
            request,
            f"{updated} product(s) moved to draft.",
            messages.WARNING,
        )

    @admin.action(description="Publish selected products")
    def publish_products(self, request, queryset):
        updated = queryset.update(is_drafted=False)
        self.message_user(
            request,
            f"{updated} product(s) published successfully.",
            messages.SUCCESS,
        )


# admin.site.register(ProductVariant)
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "is_drafted")
    list_filter = ("is_drafted",)
    actions = ["draft_variants", "publish_variants"]

    @admin.action(description="Move selected variants to draft")
    def draft_variants(self, request, queryset):
        updated = queryset.update(is_drafted=True)
        self.message_user(
            request,
            f"{updated} variant(s) moved to draft.",
            messages.WARNING,
        )

    @admin.action(description="Publish selected variants")
    def publish_variants(self, request, queryset):
        updated = queryset.update(is_drafted=False)
        self.message_user(
            request,
            f"{updated} variant(s) published successfully.",
            messages.SUCCESS,
        )


# admin.site.register(ProductImage)
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("variant", "is_primary")
