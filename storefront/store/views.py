from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from . import models
from .forms import AddressForm, AddToCartForm, CartItemUpdateForm


# Cart helpers

def _get_cart(request, create=False):
    """Fetch the current shopping cart using the id stored in the session.

    Works for both anonymous and logged-in visitors: the cart follows the
    browser session, so it persists across requests without requiring an
    account.
    """
    cart_id = request.session.get("cart_id")
    cart = None
    if cart_id:
        cart = models.Cart.objects.filter(pk=cart_id).first()
    if cart is None and create:
        cart = models.Cart.objects.create()
        request.session["cart_id"] = cart.id
    return cart


def _get_or_create_customer(user):
    customer, _ = models.Customer.objects.get_or_create(
        user=user,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email or f"user{user.pk}@example.com",
            "phone": "",
        },
    )
    return customer


# Public storefront: products, collections, search

class HomeView(TemplateView):
    template_name = "store/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_products"] = (
            models.Product.objects.filter(is_featured=True)
            .select_related("collection")
            .order_by("?")[:8]
        )
        context["new_arrivals"] = (
            models.Product.objects.select_related("collection").order_by("-id")[:8]
        )
        best_seller_ids = (
            models.OrderItem.objects.values("product")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")
            .values_list("product", flat=True)[:8]
        )
        best_sellers = models.Product.objects.filter(pk__in=list(best_seller_ids)).select_related("collection")
        # Preserve the "best selling first" order from the aggregation above.
        best_sellers_by_id = {p.id: p for p in best_sellers}
        context["best_sellers"] = [best_sellers_by_id[pk] for pk in best_seller_ids if pk in best_sellers_by_id]
        context["collections"] = models.Collection.objects.all()[:8]
        context["promotions"] = models.Promotion.objects.all()[:6]
        return context


class CollectionListView(ListView):
    model = models.Collection
    template_name = "store/collection_list.html"
    context_object_name = "collections"

    def get_queryset(self):
        return models.Collection.objects.all().order_by("title")


class ProductListView(ListView):
    model = models.Product
    template_name = "store/product_list.html"
    context_object_name = "products"
    paginate_by = 18

    def get_queryset(self):
        queryset = models.Product.objects.select_related("collection").order_by("title")
        query = self.request.GET.get("q")
        collection_id = self.request.GET.get("collection")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collections"] = models.Collection.objects.all()
        context["query"] = self.request.GET.get("q", "")
        context["selected_collection"] = self.request.GET.get("collection", "")
        return context


class ProductDetailView(DetailView):
    model = models.Product
    template_name = "store/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        queryset = (queryset or self.get_queryset()).select_related("collection").prefetch_related("images")
        product = queryset.filter(slug=self.kwargs["slug"]).first()
        if product is None:
            raise Http404("Product not found")
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["add_to_cart_form"] = AddToCartForm()
        context["related_products"] = (
            models.Product.objects.filter(collection=self.object.collection)
            .exclude(pk=self.object.pk)[:4]
        )
        return context


class CollectionDetailView(DetailView):
    model = models.Collection
    template_name = "store/collection_detail.html"
    context_object_name = "collection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.object.product_set.select_related("collection").order_by("title")
        return context


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

def cart_detail(request):
    cart = _get_cart(request, create=False)
    items = cart.items.select_related("product").all() if cart else []
    return render(request, "store/cart_detail.html", {
        "cart": cart,
        "items": items,
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(models.Product, pk=product_id)
    quantity = 1
    if request.method == "POST":
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]

    cart = _get_cart(request, create=True)
    item, created = models.CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": 0}
    )
    desired_quantity = quantity if created else item.quantity + quantity
    available = max(product.inventory, 0)

    if available <= 0:
        item.delete()
        messages.error(request, f'"{product.title}" is out of stock.')
    else:
        item.quantity = min(desired_quantity, available)
        item.save()
        if desired_quantity > available:
            messages.warning(
                request,
                f'Only {available} unit(s) of "{product.title}" are available; '
                f"your cart has been capped at that amount.",
            )
        else:
            messages.success(request, f'"{product.title}" was added to your cart.')

    next_url = request.POST.get("next") or request.GET.get("next")
    return redirect(next_url or "store:cart_detail")


@require_POST
def update_cart_item(request, item_id):
    cart = _get_cart(request, create=False)
    item = get_object_or_404(models.CartItem, pk=item_id, cart=cart)
    form = CartItemUpdateForm(request.POST, instance=item)
    if form.is_valid():
        updated_item = form.save(commit=False)
        available = max(updated_item.product.inventory, 0)
        if updated_item.quantity > available:
            updated_item.quantity = available
            messages.warning(
                request,
                f'Only {available} unit(s) of "{updated_item.product.title}" are available.',
            )
        else:
            messages.success(request, "Cart updated.")
        if updated_item.quantity <= 0:
            updated_item.delete()
        else:
            updated_item.save()
    return redirect("store:cart_detail")


@require_POST
def remove_from_cart(request, item_id):
    cart = _get_cart(request, create=False)
    item = get_object_or_404(models.CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect("store:cart_detail")


# ---------------------------------------------------------------------------
# Checkout & orders
# ---------------------------------------------------------------------------

@login_required
def checkout(request):
    customer = _get_or_create_customer(request.user)
    address = getattr(customer, "address", None)
    cart = _get_cart(request, create=False)
    items = list(cart.items.select_related("product").all()) if cart else []

    if not items:
        messages.warning(request, "Your cart is empty. Add some products before checking out.")
        return redirect("store:product_list")

    if request.method == "POST":
        address_form = AddressForm(request.POST, instance=address)

        out_of_stock = [item for item in items if item.quantity > item.product.inventory]
        if out_of_stock:
            for item in out_of_stock:
                messages.error(
                    request,
                    f'Only {item.product.inventory} unit(s) of "{item.product.title}" are left in stock. '
                    f"Please update your cart.",
                )
            return redirect("store:cart_detail")

        if address_form.is_valid():
            with transaction.atomic():
                new_address = address_form.save(commit=False)
                new_address.customer = customer
                new_address.save()

                order = models.Order.objects.create(customer=customer)
                for item in items:
                    models.OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.product.unit_price,
                    )
                    models.Product.objects.filter(pk=item.product_id).update(
                        inventory=F("inventory") - item.quantity
                    )
                cart.items.all().delete()
                cart.delete()
                if "cart_id" in request.session:
                    del request.session["cart_id"]

            messages.success(request, "Your order has been placed successfully!")
            return redirect("store:order_confirmation", pk=order.pk)
    else:
        address_form = AddressForm(instance=address)

    total_price = sum(item.total_price for item in items)
    return render(request, "store/checkout.html", {
        "address_form": address_form,
        "items": items,
        "total_price": total_price,
    })


class OrderConfirmationView(LoginRequiredMixin, DetailView):
    model = models.Order
    template_name = "store/order_confirmation.html"
    context_object_name = "order"

    def get_queryset(self):
        customer = _get_or_create_customer(self.request.user)
        return models.Order.objects.filter(customer=customer).prefetch_related("orderitem_set__product")


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = models.Order
    template_name = "store/order_history.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        customer = _get_or_create_customer(self.request.user)
        return (
            models.Order.objects.filter(customer=customer)
            .prefetch_related("orderitem_set__product")
            .order_by("-placed_at")
        )
