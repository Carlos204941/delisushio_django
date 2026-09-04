from django import forms
from django.utils import timezone
from .models import DeliveryAddress, Order


class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ['street', 'number', 'postal_code', 'phone_number', 'delivery_zone', 'delivery_instructions']
        widgets = {
            'delivery_instructions': forms.Textarea(attrs={'rows': 3}),
        }


class CheckoutForm(forms.Form):
    delivery_address = forms.ModelChoiceField(queryset=DeliveryAddress.objects.none(), empty_label=None)
    delivery_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    allergens_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['delivery_address'].queryset = DeliveryAddress.objects.filter(user=user)

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data['delivery_date']
        if delivery_date <= timezone.now():
            raise forms.ValidationError('Delivery date must be in the future.')
        return delivery_date


class CartItemUpdateForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
