from .models import Cart


def cart(request):
    """Make the current cart's item count available in every template."""
    cart_id = request.session.get("cart_id")
    count = 0
    if cart_id:
        current_cart = Cart.objects.filter(pk=cart_id).first()
        if current_cart:
            count = current_cart.total_items
    return {"cart_items_count": count}
