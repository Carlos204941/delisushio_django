from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/item/<int:item_id>/update/', views.cart_item_update_view, name='cart_item_update'),
    path('cart/item/<int:item_id>/remove/', views.cart_item_remove_view, name='cart_item_remove'),

    # Delivery addresses
    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/new/', views.address_create_view, name='address_create'),
    path('addresses/<int:pk>/edit/', views.address_update_view, name='address_update'),
    path('addresses/<int:pk>/delete/', views.address_delete_view, name='address_delete'),

    # Orders (CRUD)
    path('checkout/', views.checkout_view, name='checkout'),
    path('', views.order_list_view, name='list'),
    path('<uuid:pk>/', views.order_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.order_update_view, name='update'),
    path('<uuid:pk>/delete/', views.order_delete_view, name='delete'),
    path('admin/received/<uuid:pk>/confirm/', views.admin_confirm_order_received_view, name='admin_confirm_received'),
    path('admin/pending-count/', views.admin_pending_orders_count_view, name='admin_pending_count'),
]
