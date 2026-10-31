from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import models


class ProductModelTests(TestCase):
    def setUp(self):
        self.collection = models.Collection.objects.create(title="Electronics")
        self.product = models.Product.objects.create(
            title="Wireless Mouse",
            slug="wireless-mouse",
            description="A mouse.",
            unit_price=19.99,
            inventory=10,
            collection=self.collection,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Wireless Mouse")

    def test_cart_totals(self):
        self.product.refresh_from_db()
        cart = models.Cart.objects.create()
        models.CartItem.objects.create(cart=cart, product=self.product, quantity=3)
        self.assertEqual(cart.total_items, 3)
        self.assertEqual(cart.total_price, self.product.unit_price * 3)


class CartViewTests(TestCase):
    def setUp(self):
        self.collection = models.Collection.objects.create(title="Electronics")
        self.product = models.Product.objects.create(
            title="Wireless Mouse",
            slug="wireless-mouse",
            description="A mouse.",
            unit_price=19.99,
            inventory=5,
            collection=self.collection,
        )

    def test_product_list_page_loads(self):
        response = self.client.get(reverse("store:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wireless Mouse")

    def test_product_detail_page_loads(self):
        response = self.client.get(
            reverse("store:product_detail", kwargs={"slug": self.product.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_search_filters_results(self):
        models.Product.objects.create(
            title="Keyboard", slug="keyboard", description="A keyboard.",
            unit_price=39.99, inventory=5, collection=self.collection,
        )
        response = self.client.get(reverse("store:product_list"), {"q": "Mouse"})
        products = list(response.context["products"])
        self.assertEqual(products, [self.product])

    def test_add_to_cart_creates_cart_item(self):
        response = self.client.post(
            reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 2}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.CartItem.objects.count(), 1)
        self.assertEqual(models.CartItem.objects.first().quantity, 2)

    def test_add_to_cart_is_capped_at_available_inventory(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 999})
        item = models.CartItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, self.product.inventory)

    def test_remove_from_cart(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        item = models.CartItem.objects.get(product=self.product)
        self.client.post(reverse("store:remove_from_cart", args=[item.id]))
        self.assertEqual(models.CartItem.objects.count(), 0)


class CheckoutTests(TestCase):
    def setUp(self):
        self.collection = models.Collection.objects.create(title="Electronics")
        self.product = models.Product.objects.create(
            title="Wireless Mouse", slug="wireless-mouse", description="A mouse.",
            unit_price=19.99, inventory=5, collection=self.collection,
        )
        self.user = User.objects.create_user(
            username="ada", password="SuperSecret123!", email="ada@example.com"
        )

    def test_checkout_requires_login(self):
        response = self.client.get(reverse("store:checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_checkout_creates_order_and_decrements_inventory(self):
        self.client.login(username="ada", password="SuperSecret123!")
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 2})

        response = self.client.post(
            reverse("store:checkout"), {"street": "123 Main St", "city": "Springfield"}
        )
        self.assertEqual(response.status_code, 302)

        order = models.Order.objects.get(customer__user=self.user)
        self.assertEqual(order.orderitem_set.count(), 1)
        self.assertEqual(order.orderitem_set.first().quantity, 2)

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 3)

        # cart should be cleared after a successful checkout
        self.assertEqual(models.CartItem.objects.count(), 0)

    def test_customer_auto_created_for_new_user(self):
        self.assertTrue(models.Customer.objects.filter(user=self.user).exists())
