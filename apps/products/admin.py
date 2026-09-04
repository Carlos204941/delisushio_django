from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id_product', 'name', 'category', 'price', 'stock_quantity', 'is_available', 'spice_level']
    list_filter = ['category', 'spice_level', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock_quantity', 'is_available']
    ordering = ['category', 'name']
