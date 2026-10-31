from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode
from . import models


class InventoryFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"

    def lookups(self, request, model_admin):
        return [
            ("<10", "Low"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "<10":
            return queryset.filter(inventory__lt=10)


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    extra = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    autocomplete_fields = ["collection"]
    prepopulated_fields = {"slug": ["title"]}
    actions = ["clear_inventory", "mark_as_featured", "unmark_as_featured"]
    inlines = [ProductImageInline]
    list_display = [
        "title", "unit_price", "inventory_status", "collection_title",
        "is_featured", "stock_value",
    ]
    list_editable = ["unit_price", "is_featured"]
    list_filter = ["collection", "is_featured", "last_update", InventoryFilter]
    list_per_page = 20
    list_select_related = ["collection"]
    search_fields = ["title"]

    def collection_title(self, product):
        return product.collection.title

    @admin.display(ordering="inventory")
    def inventory_status(self, product):
        if product.inventory < 10:
            return "Low"
        return "OK"

    @admin.display(description="Stock value")
    def stock_value(self, product):
        return f"${product.inventory * product.unit_price:,.2f}"

    @admin.action(description="Clear inventory")
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f"{updated_count} products were successfully updated.",
        )

    @admin.action(description="Mark selected products as featured")
    def mark_as_featured(self, request, queryset):
        updated_count = queryset.update(is_featured=True)
        self.message_user(request, f"{updated_count} products marked as featured.")

    @admin.action(description="Remove selected products from featured")
    def unmark_as_featured(self, request, queryset):
        updated_count = queryset.update(is_featured=False)
        self.message_user(request, f"{updated_count} products removed from featured.")


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]
    list_display = ["first_name", "last_name", "membership", "orders_count"]
    list_editable = ["membership"]
    ordering = ["first_name", "last_name"]
    search_fields = ["first_name__istartswith", "last_name__istartswith"]
    list_per_page = 10

    @admin.display(ordering="orders_count")
    def orders_count(self, customer):
        url = (
            reverse("admin:store_order_changelist")
            + "?"
            + urlencode({"customer__id": str(customer.id)})
        )
        return format_html('<a href="{}">{}</a>', url, customer.orders_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            orders_count=Count("order")
        )


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    min_num = 1
    max_num = 10
    model = models.OrderItem
    extra = 0


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ["customer"]
    inlines = [OrderItemInline]
    list_display = ["id", "placed_at", "payment_status", "customer", "order_total"]
    list_editable = ["payment_status"]
    list_filter = ["payment_status"]
    list_per_page = 20
    date_hierarchy = "placed_at"

    @admin.display(description="Total")
    def order_total(self, order):
        return f"${order.total_price:,.2f}"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("orderitem_set")


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["featured_product"]
    list_display = ["title", "products_count"]
    search_fields = ["title"]

    @admin.display(ordering="products_count")
    def products_count(self, collection):
        url = (
            reverse("admin:store_product_changelist")
            + "?"
            + urlencode({"collection__id": str(collection.id)})
        )
        return format_html('<a href="{}">{}</a>', url, collection.products_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count("product")
        )


@admin.register(models.Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ["description", "discount"]
    search_fields = ["description"]
    ordering = ["-discount"]


class CartItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    model = models.CartItem
    extra = 0


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ["id", "created_at", "item_count", "cart_total"]
    list_filter = ["created_at"]
    list_per_page = 20

    @admin.display(description="Items")
    def item_count(self, cart):
        return cart.total_items

    @admin.display(description="Total")
    def cart_total(self, cart):
        return f"${cart.total_price:,.2f}"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items__product")


@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    autocomplete_fields = ["product"]
    list_display = ["cart", "product", "quantity"]
    list_filter = ["product__collection"]
    search_fields = ["product__title"]


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    autocomplete_fields = ["customer"]
    list_display = ["customer", "street", "city"]
    search_fields = ["street", "city", "customer__first_name", "customer__last_name"]
