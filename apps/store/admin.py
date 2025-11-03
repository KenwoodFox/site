from django.contrib import admin
from .models import StoreItem, StoreImage


class StoreImageInline(admin.TabularInline):
    model = StoreImage
    extra = 1
    fields = ("image", "alt_text", "order")


@admin.register(StoreItem)
class StoreItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "price",
        "in_stock",
        "stock_quantity",
        "published_at",
    )
    list_filter = ("status", "in_stock", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [StoreImageInline]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "slug", "description")}),
        ("Pricing", {"fields": ("price", "currency")}),
        ("Inventory", {"fields": ("in_stock", "stock_quantity")}),
        ("Status", {"fields": ("status", "published_at")}),
        ("Media", {"fields": ("featured_image",)}),
    )


@admin.register(StoreImage)
class StoreImageAdmin(admin.ModelAdmin):
    list_display = ("item", "order", "alt_text", "created_at")
    list_filter = ("created_at",)
    search_fields = ("item__title", "alt_text")
