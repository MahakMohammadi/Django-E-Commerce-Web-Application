# The accounts app relies on Django's built-in auth.User model together with
# store.models.Customer (linked via a OneToOneField, kept in sync through the
# post_save signal in store/signals.py). No additional models are needed here.
