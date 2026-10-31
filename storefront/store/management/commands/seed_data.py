import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from store import models as store_models
from store.product_images import generate_product_image
from tags import models as tag_models

fake = Faker()

TARGET_COLLECTIONS = 15
TARGET_PRODUCTS = 220
TARGET_PROMOTIONS = 10
TARGET_TAGS = 12
TARGET_CUSTOMERS = 40
TARGET_ORDERS = 90
TARGET_CARTS = 8

COLLECTION_CATALOG = {
    "Electronics": ["Headphones", "Bluetooth Speaker", "Smartwatch", "Laptop Stand",
                    "Webcam", "Wi-Fi Router", "Power Bank", "Tablet", "USB-C Charger", "Wireless Mouse"],
    "Home & Kitchen": ["Blender", "Toaster", "Cookware Set", "Knife Set", "Coffee Maker",
                       "Cutting Board", "Mixing Bowl", "Air Fryer", "Electric Kettle", "Dish Rack"],
    "Books": ["Novel", "Cookbook", "Biography", "Journal", "Notebook",
              "Textbook", "Comic Book", "Poetry Collection", "Travel Guidebook", "Encyclopedia"],
    "Clothing": ["T-Shirt", "Denim Jacket", "Jeans", "Wool Sweater", "Hoodie",
                 "Summer Dress", "Scarf", "Ankle Socks", "Sun Hat", "Cargo Shorts"],
    "Sports & Outdoors": ["Yoga Mat", "Dumbbell Set", "Camping Tent", "Hiking Backpack",
                          "Water Bottle", "Bicycle Helmet", "Running Shoes", "Camping Chair",
                          "Fishing Rod", "Sleeping Bag"],
    "Toys & Games": ["Jigsaw Puzzle", "Board Game", "Action Figure", "Building Blocks Set",
                     "Card Game", "Plush Toy", "RC Car", "Collectible Doll", "Toy Train Set", "Kite"],
    "Beauty & Personal Care": ["Shampoo", "Face Cream", "Lipstick", "Perfume", "Hair Dryer",
                               "Electric Razor", "Nail Polish Set", "Sunscreen", "Body Lotion",
                               "Makeup Brush Set"],
    "Automotive": ["Car Vacuum", "Phone Mount", "Seat Cover", "Tire Pressure Gauge",
                   "Jump Starter", "Dash Cam", "Floor Mat Set", "Air Freshener", "Car Cover", "Tool Kit"],
    "Garden & Outdoor": ["Garden Hose", "Lawn Mower", "Ceramic Plant Pot", "Pruning Shears",
                         "Patio Umbrella", "Bird Feeder", "Wheelbarrow", "Garden Gloves",
                         "Watering Can", "Outdoor Lantern"],
    "Office Supplies": ["Desk Organizer", "Stapler", "Notebook Set", "Pen Set", "Whiteboard",
                        "Office Chair", "LED Desk Lamp", "File Folder Set", "Sticky Notes", "Calculator"],
    "Pet Supplies": ["Dog Bed", "Cat Tower", "Pet Carrier", "Retractable Leash", "Ceramic Pet Bowl",
                     "Aquarium Filter", "Bird Cage", "Chew Toy", "Litter Box", "Pet Grooming Brush"],
    "Health & Wellness": ["Vitamin Pack", "Yoga Block", "Massage Gun", "Digital Thermometer",
                          "First Aid Kit", "Resistance Bands", "Blood Pressure Monitor",
                          "Essential Oil Set", "Foam Roller", "Sleep Mask"],
    "Music & Instruments": ["Acoustic Guitar", "Keyboard Piano", "Drum Sticks", "USB Microphone",
                            "Guitar Strings", "Ukulele", "Music Stand", "Metronome",
                            "Headphone Amp", "Harmonica"],
    "Grocery": ["Coffee Beans", "Olive Oil", "Pasta Pack", "Spice Set", "Tea Collection",
                "Granola", "Honey Jar", "Snack Box", "Rice Bag", "Chocolate Box"],
    "Jewelry": ["Necklace", "Bracelet", "Earrings", "Ring", "Wrist Watch",
                "Pendant", "Anklet", "Cufflinks", "Brooch", "Hair Pin"],
}

ADJECTIVES = [
    "Premium", "Deluxe", "Classic", "Modern", "Compact", "Portable", "Professional",
    "Eco-Friendly", "Wireless", "Rechargeable", "Handcrafted", "Vintage", "Smart",
    "Ultra", "Ergonomic", "Everyday", "Signature", "Essential", "Travel-Size", "Heavy-Duty",
]

TAG_NAMES = [
    "New Arrival", "Best Seller", "Sale", "Eco-Friendly", "Limited Edition", "Staff Pick",
    "Trending", "Premium", "Budget Friendly", "Gift Idea", "Handmade", "Clearance",
]

PROMOTION_TEMPLATES = [
    ("Summer Sale", 0.15), ("Black Friday Deal", 0.30), ("Clearance", 0.40),
    ("New Customer Discount", 0.10), ("Flash Sale", 0.20), ("Holiday Special", 0.25),
    ("Bundle Discount", 0.12), ("Loyalty Reward", 0.10), ("End of Season", 0.35),
    ("Weekend Special", 0.18),
]


class Command(BaseCommand):
    help = "Populate the database with realistic demo data (collections, products, images, promotions, tags, customers, orders, carts)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products", type=int, default=TARGET_PRODUCTS,
            help="Target total number of products (default: %(default)s).",
        )

    def handle(self, *args, **options):
        target_products = options["products"]
        Faker.seed()

        with transaction.atomic():
            self.stdout.write("Seeding demo admin user...")
            self._seed_superuser()

            self.stdout.write("Seeding collections...")
            collections = self._seed_collections()

            self.stdout.write("Seeding promotions...")
            promotions = self._seed_promotions()

            self.stdout.write("Seeding tags...")
            tags = self._seed_tags()

            self.stdout.write(f"Seeding products (target: {target_products})...")
            products = self._seed_products(collections, promotions, tags, target_products)

            self.stdout.write("Seeding product images...")
            self._seed_images(products)

            self.stdout.write("Marking featured products...")
            self._seed_featured(products)

            self.stdout.write("Seeding demo customers & addresses...")
            customers = self._seed_customers()

            self.stdout.write("Seeding orders & order items...")
            self._seed_orders(customers, products)

            self.stdout.write("Seeding demo (abandoned) carts...")
            self._seed_carts(products)

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))
        self.stdout.write(self.style.SUCCESS(
            f"Collections: {store_models.Collection.objects.count()} | "
            f"Products: {store_models.Product.objects.count()} | "
            f"Customers: {store_models.Customer.objects.count()} | "
            f"Orders: {store_models.Order.objects.count()}"
        ))

    # ------------------------------------------------------------------
    def _seed_superuser(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "Admin12345!")
            self.stdout.write(self.style.SUCCESS('  Created superuser "admin" / "Admin12345!"'))
        else:
            self.stdout.write('  Superuser "admin" already exists, skipping.')

    def _seed_collections(self):
        names = list(COLLECTION_CATALOG.keys())[:TARGET_COLLECTIONS]
        collections = []
        for name in names:
            collection, _ = store_models.Collection.objects.get_or_create(title=name)
            collections.append(collection)
        return collections

    def _seed_promotions(self):
        promotions = []
        for description, discount in PROMOTION_TEMPLATES[:TARGET_PROMOTIONS]:
            promotion, _ = store_models.Promotion.objects.get_or_create(
                description=description, defaults={"discount": discount}
            )
            promotions.append(promotion)
        return promotions

    def _seed_tags(self):
        tags = []
        for label in TAG_NAMES[:TARGET_TAGS]:
            tag, _ = tag_models.Tag.objects.get_or_create(label=label)
            tags.append(tag)
        return tags

    def _unique_slug(self, title, used_slugs):
        base = slugify(title)
        slug = base
        counter = 2
        while slug in used_slugs:
            slug = f"{base}-{counter}"
            counter += 1
        used_slugs.add(slug)
        return slug

    def _seed_products(self, collections, promotions, tags, target_products):
        existing = store_models.Product.objects.count()
        if existing >= target_products:
            self.stdout.write(f"  Already have {existing} products, skipping product creation.")
            return list(store_models.Product.objects.all())

        used_slugs = set(store_models.Product.objects.values_list("slug", flat=True))
        content_type = ContentType.objects.get_for_model(store_models.Product)
        to_create = target_products - existing
        per_collection = max(1, to_create // len(collections))

        created_products = []
        for collection in collections:
            noun_bank = COLLECTION_CATALOG.get(collection.title, ["Item"])
            for _ in range(per_collection):
                noun = random.choice(noun_bank)
                adjective = random.choice(ADJECTIVES)
                title = f"{adjective} {noun}"
                slug = self._unique_slug(title, used_slugs)

                product = store_models.Product.objects.create(
                    title=title,
                    slug=slug,
                    description=fake.paragraph(nb_sentences=4),
                    unit_price=round(random.uniform(7.99, 499.99), 2),
                    inventory=random.choice([0, 0] + list(range(1, 120))),
                    collection=collection,
                )

                if random.random() < 0.35:
                    product.promotion.set(random.sample(promotions, k=random.randint(1, 2)))

                if random.random() < 0.4:
                    chosen_tags = random.sample(tags, k=random.randint(1, 3))
                    for tag in chosen_tags:
                        tag_models.TaggedItem.objects.get_or_create(
                            tag=tag, content_type=content_type, object_id=product.id
                        )

                created_products.append(product)

        self.stdout.write(f"  Created {len(created_products)} products.")
        return list(store_models.Product.objects.all())

    def _seed_images(self, products):
        products_needing_images = [p for p in products if not p.images.exists()]
        count = 0
        for product in products_needing_images:
            for i in range(random.randint(1, 2)):
                filename, content = generate_product_image(
                    product.title, product.collection.title, seed=f"{product.id}-{i}"
                )
                image = store_models.ProductImage(product=product)
                image.image.save(filename, content, save=True)
                count += 1
        self.stdout.write(f"  Generated {count} product images.")

    def _seed_featured(self, products):
        if store_models.Product.objects.filter(is_featured=True).count() >= 12:
            return
        candidates = random.sample(products, k=min(18, len(products)))
        for product in candidates:
            product.is_featured = True
            product.save(update_fields=["is_featured"])

    def _seed_customers(self):
        existing = store_models.Customer.objects.filter(user__isnull=True).count()
        if existing >= TARGET_CUSTOMERS:
            self.stdout.write(f"  Already have {existing} demo customers, skipping.")
            return list(store_models.Customer.objects.filter(user__isnull=True))

        customers = []
        for _ in range(TARGET_CUSTOMERS - existing):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()
            membership = random.choices(
                [store_models.Customer.MEMBERSHIP_BRONZE,
                 store_models.Customer.MEMBERSHIP_SILVER,
                 store_models.Customer.MEMBERSHIP_GOLD],
                weights=[60, 30, 10],
            )[0]
            customer = store_models.Customer.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=fake.phone_number()[:255],
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
                membership=membership,
            )
            store_models.Address.objects.get_or_create(
                customer=customer,
                defaults={"street": fake.street_address(), "city": fake.city()},
            )
            customers.append(customer)

        self.stdout.write(f"  Created {len(customers)} demo customers.")
        return list(store_models.Customer.objects.filter(user__isnull=True))

    def _seed_orders(self, customers, products):
        existing = store_models.Order.objects.count()
        if existing >= TARGET_ORDERS or not customers:
            self.stdout.write(f"  Already have {existing} orders, skipping.")
            return

        in_stock_products = [p for p in products if p.inventory > 0] or products
        statuses = (
            [store_models.Order.PAYMENT_COMPLETE] * 7
            + [store_models.Order.PAYMENT_PENDING] * 2
            + [store_models.Order.PAYMENT_FAILED] * 1
        )

        created = 0
        for _ in range(TARGET_ORDERS - existing):
            customer = random.choice(customers)
            order = store_models.Order.objects.create(
                customer=customer,
                payment_status=random.choice(statuses),
            )
            # Backdate the order for a more realistic order history; auto_now_add
            # only applies on the initial save(), so a follow-up update() is safe.
            placed_at = timezone.now() - timedelta(days=random.randint(0, 120))
            store_models.Order.objects.filter(pk=order.pk).update(placed_at=placed_at)

            for product in random.sample(in_stock_products, k=min(random.randint(1, 4), len(in_stock_products))):
                store_models.OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 3),
                    unit_price=product.unit_price,
                )
            created += 1

        self.stdout.write(f"  Created {created} orders.")

    def _seed_carts(self, products):
        if store_models.Cart.objects.count() >= TARGET_CARTS:
            self.stdout.write("  Already have enough demo carts, skipping.")
            return

        for _ in range(TARGET_CARTS - store_models.Cart.objects.count()):
            cart = store_models.Cart.objects.create()
            for product in random.sample(products, k=min(random.randint(1, 3), len(products))):
                store_models.CartItem.objects.get_or_create(
                    cart=cart, product=product,
                    defaults={"quantity": random.randint(1, 2)},
                )
        self.stdout.write("  Seeded demo abandoned carts.")
