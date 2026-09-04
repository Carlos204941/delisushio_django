from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Product, Category
from apps.orders.models import Cart, CartItem


def product_list_view(request):
    products = Product.objects.filter(is_available=True)
    category = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    if search_query:
        products = products.filter(name__icontains=search_query)
    if category:
        products = products.filter(category=category)
    context = {
        'products': products,
        'categories': Category.choices,
        'selected_category': category,
        'search_query': search_query,
    }
    return render(request, 'products/list.html', context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    return render(request, 'products/detail.html', {'product': product})


@login_required
def add_to_cart_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    if request.method == 'POST':
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1

        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'product_name_snapshot': product.name,
                'category_snapshot': product.category,
            },
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity'])

        messages.success(request, f'Added {product.name} to your cart.')

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('orders:cart')
