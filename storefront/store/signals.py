from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_new_user(sender, instance, created, **kwargs):
    """Automatically create a matching Customer profile whenever a new User registers."""
    if created:
        models.Customer.objects.get_or_create(
            user=instance,
            defaults={
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "email": instance.email or f"user{instance.pk}@example.com",
                "phone": "",
            },
        )
