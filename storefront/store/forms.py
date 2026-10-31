from django import forms

from . import models


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "style": "width: 6rem;"}),
    )


class CartItemUpdateForm(forms.ModelForm):
    class Meta:
        model = models.CartItem
        fields = ["quantity"]
        widgets = {
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "style": "width: 6rem;", "min": 1}
            ),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = models.Address
        fields = ["street", "city"]
        widgets = {
            "street": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street address"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
        }
