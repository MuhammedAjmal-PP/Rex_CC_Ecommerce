from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "title", "is_active", "created_at")
    list_filter = ("rating", "is_active", "created_at")
    search_fields = ("user__email", "product__name", "title", "comment")
    list_editable = ("is_active",)
    readonly_fields = ("user", "product", "rating", "title", "comment", "created_at", "updated_at")
    ordering = ("-created_at",)
