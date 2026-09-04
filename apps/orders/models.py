from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.products.models import Product
import uuid


class DeliveryAddress(models.Model):
    id_delivery = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    delivery_zone = models.CharField(max_length=100)
    delivery_instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.street} {self.number}, {self.postal_code}"


class Cart(models.Model):
    id_cart = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id_cart} ({self.user.email})"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    # Snapshot of data at the time it was added to cart
    product_name_snapshot = models.CharField(max_length=200)
    category_snapshot = models.CharField(max_length=10)

    class Meta:
        unique_together = ('cart', 'product')

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name_snapshot}"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id_order = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.ForeignKey(DeliveryAddress, on_delete=models.SET_NULL, null=True)

    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    promotion_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Order specific details
    delivery_date = models.DateTimeField()
    allergens_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_total(self):
        self.subtotal = sum(
            (item.unit_price * item.quantity for item in self.items.all()),
            start=Decimal('0.00'),
        )
        self.total = self.subtotal - Decimal(self.promotion_discount)
        self.save()

    def __str__(self):
        return f"Order {self.id_order} ({self.get_status_display()})"


class OrderItem(models.Model):
    """Snapshot of the cart items at the moment of purchase"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
