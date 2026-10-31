from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, RedirectView, TemplateView

from store import models as store_models

from .forms import RegistrationForm


class AccountsHomeView(RedirectView):
    """Route /accounts/ to the profile page (logged in) or the login page (anonymous)."""

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse_lazy("accounts:profile")
        return reverse_lazy("accounts:login")


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your account was created. Please log in.")
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    login_url = "accounts:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer, _ = store_models.Customer.objects.get_or_create(
            user=self.request.user,
            defaults={
                "first_name": self.request.user.first_name,
                "last_name": self.request.user.last_name,
                "email": self.request.user.email or f"user{self.request.user.pk}@example.com",
                "phone": "",
            },
        )
        context["customer"] = customer
        context["address"] = getattr(customer, "address", None)
        context["recent_orders"] = customer.order_set.order_by("-placed_at")[:5]
        return context
