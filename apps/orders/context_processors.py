from .models import Order


def superuser_order_notifications(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated or not request.user.is_superuser:
        return {
            'superuser_pending_orders': [],
            'superuser_pending_orders_count': 0,
        }

    pending_orders = list(
        Order.objects.filter(status=Order.OrderStatus.PENDING)
        .select_related('user', 'delivery_address')
        .only('id_order', 'created_at', 'delivery_date', 'user__email', 'delivery_address__delivery_zone')
        .order_by('-created_at')[:12]
    )

    return {
        'superuser_pending_orders': pending_orders,
        'superuser_pending_orders_count': len(pending_orders),
    }