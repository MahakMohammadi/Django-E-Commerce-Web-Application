from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("collections/", views.CollectionListView.as_view(), name="collection_list"),
    path("collections/<int:pk>/", views.CollectionDetailView.as_view(), name="collection_detail"),

    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),

    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.OrderHistoryView.as_view(), name="order_history"),
    path("orders/<int:pk>/", views.OrderConfirmationView.as_view(), name="order_confirmation"),
]
