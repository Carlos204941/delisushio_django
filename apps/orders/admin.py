from django.contrib import admin
from .models import DeliveryAddress, Cart, CartItem, Order, OrderItem


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ['id_delivery', 'user', 'street', 'number', 'postal_code', 'delivery_zone']
    search_fields = ['user__email', 'street', 'postal_code', 'delivery_zone']
    list_filter = ['delivery_zone']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product_name_snapshot', 'category_snapshot']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id_cart', 'user', 'item_count', 'total', 'updated_at']
    inlines = [CartItemInline]
    search_fields = ['user__email']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'category', 'unit_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id_order', 'user', 'status', 'total', 'delivery_date', 'created_at']
    list_filter = ['status', 'delivery_date']
    search_fields = ['id_order', 'user__email']
    list_editable = ['status']
    readonly_fields = ['id_order', 'subtotal', 'total', 'created_at']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
