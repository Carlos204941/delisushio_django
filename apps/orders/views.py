from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from django.views.decorators.http import require_GET, require_POST

from .models import Cart, CartItem, DeliveryAddress, Order, OrderItem
from .forms import DeliveryAddressForm, CheckoutForm, CartItemUpdateForm, OrderStatusForm


# ---------- Cart ----------

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = list(cart.items.select_related('product'))
    cart_total = sum((item.subtotal for item in cart_items), start=Decimal('0.00'))
    return render(
        request,
        'orders/cart.html',
        {
            'cart': cart,
            'cart_items': cart_items,
            'cart_total': cart_total,
        },
    )


@login_required
def cart_item_update_view(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        form = CartItemUpdateForm(request.POST)
        if form.is_valid():
            item.quantity = form.cleaned_data['quantity']
            item.save(update_fields=['quantity'])
            messages.success(request, 'Cart updated.')
    return redirect('orders:cart')


@login_required
def cart_item_remove_view(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.info(request, 'Item removed from cart.')
    return redirect('orders:cart')


# ---------- Delivery addresses ----------

@login_required
def address_list_view(request):
    addresses = DeliveryAddress.objects.filter(user=request.user)
    return render(request, 'orders/address_list.html', {'addresses': addresses})


@login_required
def address_create_view(request):
    if request.method == 'POST':
        form = DeliveryAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address saved.')
            return redirect('orders:address_list')
    else:
        form = DeliveryAddressForm()
    return render(request, 'orders/address_form.html', {'form': form, 'is_new': True})


@login_required
def address_update_view(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DeliveryAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('orders:address_list')
    else:
        form = DeliveryAddressForm(instance=address)
    return render(request, 'orders/address_form.html', {'form': form, 'is_new': False})


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.info(request, 'Address deleted.')
        return redirect('orders:address_list')
    return render(request, 'orders/address_confirm_delete.html', {'address': address})


# ---------- Orders (CRUD) ----------

@login_required
def checkout_view(request):
    """Create: turns the current cart into an Order + OrderItems."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:cart')

    if not DeliveryAddress.objects.filter(user=request.user).exists():
        messages.warning(request, 'Add a delivery address before checking out.')
        return redirect('orders:address_create')

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    delivery_address=form.cleaned_data['delivery_address'],
                    delivery_date=form.cleaned_data['delivery_date'],
                    allergens_notes=form.cleaned_data['allergens_notes'],
                )
                for cart_item in cart.items.select_related('product'):
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        product_name=cart_item.product_name_snapshot,
                        category=cart_item.category_snapshot,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.product.price,
                    )
                order.calculate_total()
                cart.items.all().delete()

            messages.success(request, 'Order placed! Thanks for your order.')
            return redirect('orders:detail', pk=order.id_order)
    else:
        form = CheckoutForm(user=request.user)

    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_list_view(request):
    """Read: list the current user's orders."""
    orders = Order.objects.filter(user=request.user).only(
        'id_order',
        'status',
        'total',
        'delivery_date',
    )
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, pk):
    """Read: a single order's detail."""
    order = get_object_or_404(
        Order.objects.select_related('delivery_address').prefetch_related('items'),
        pk=pk,
        user=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_update_view(request, pk):
    """Update: change an order's status (while it's still editable)."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status not in (Order.OrderStatus.PENDING, Order.OrderStatus.CONFIRMED):
        messages.error(request, 'This order can no longer be modified.')
        return redirect('orders:detail', pk=order.id_order)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order updated.')
            return redirect('orders:detail', pk=order.id_order)
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'orders/order_form.html', {'form': form, 'order': order})


@login_required
def order_delete_view(request, pk):
    """Delete: cancel/remove a pending order."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST':
        if order.status == Order.OrderStatus.PENDING:
            order.delete()
            messages.info(request, 'Order cancelled and deleted.')
        elif order.status == Order.OrderStatus.DELIVERED:
            messages.error(request, 'Delivered orders cannot be cancelled.')
            return redirect('orders:detail', pk=order.id_order)
        elif order.status == Order.OrderStatus.CANCELLED:
            messages.info(request, 'This order is already cancelled.')
        else:
            order.status = Order.OrderStatus.CANCELLED
            order.save(update_fields=['status'])
            messages.info(request, 'Order cancelled.')
        return redirect('orders:list')
    return render(request, 'orders/order_confirm_delete.html', {'order': order})


@require_POST
@staff_member_required
def admin_confirm_order_received_view(request, pk):
    """Superuser/staff action: mark a pending order as confirmed."""
    order = get_object_or_404(Order, pk=pk)
    if order.status != Order.OrderStatus.PENDING:
        messages.info(request, 'This order is not pending anymore.')
        return redirect('products:list')

    order.status = Order.OrderStatus.CONFIRMED
    order.save(update_fields=['status'])
    messages.success(request, f'Order {order.id_order} confirmed as received.')
    return redirect('products:list')


@require_GET
@staff_member_required
def admin_pending_orders_count_view(request):
    pending_count = Order.objects.filter(status=Order.OrderStatus.PENDING).count()
    return JsonResponse({'pending_count': pending_count})
