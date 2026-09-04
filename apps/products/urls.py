from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='list'),
    path('<int:pk>/', views.product_detail_view, name='detail'),
    path('<int:pk>/add-to-cart/', views.add_to_cart_view, name='add_to_cart'),
]
