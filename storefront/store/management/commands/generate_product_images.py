from django.core.management.base import BaseCommand
from django.db import transaction

from store import models as store_models
from store.product_images import generate_product_image


class Command(BaseCommand):
    help = (
        "Ensure every product has at least one relevant, category-matched image. "
        "By default only products with no images are filled in; pass --regenerate "
        "to replace ALL existing product images with freshly generated ones."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--regenerate", action="store_true",
            help="Delete existing product images first and regenerate all of them.",
        )
        parser.add_argument(
            "--per-product", type=int, default=2,
            help="How many images to generate per product (default: %(default)s).",
        )

    def handle(self, *args, **options):
        regenerate = options["regenerate"]
        per_product = max(1, options["per_product"])

        products = store_models.Product.objects.select_related("collection").all()
        total = products.count()

        if regenerate:
            self.stdout.write(f"Regenerating images for all {total} products...")
        else:
            products = products.filter(images__isnull=True).distinct()
            self.stdout.write(f"Generating images for {products.count()} of {total} products missing images...")

        created = 0
        with transaction.atomic():
            for product in products:
                if regenerate:
                    product.images.all().delete()
                for i in range(per_product):
                    filename, content = generate_product_image(
                        product.title, product.collection.title, seed=f"{product.id}-{i}"
                    )
                    image = store_models.ProductImage(product=product)
                    image.image.save(filename, content, save=True)
                    created += 1

        missing = store_models.Product.objects.filter(images__isnull=True).distinct().count()
        self.stdout.write(self.style.SUCCESS(f"Generated {created} image(s)."))
        if missing:
            self.stdout.write(self.style.WARNING(f"{missing} product(s) still have no image."))
        else:
            self.stdout.write(self.style.SUCCESS("Every product now has at least one image."))
