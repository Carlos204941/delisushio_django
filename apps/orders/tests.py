from decimal import Decimal
from datetime import timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import CustomUser
from apps.products.models import Product, Category, SpiceLevel

from .models import DeliveryAddress, Order, Cart, CartItem, OrderItem
from .forms import CheckoutForm


class OrderCancellationRulesTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='orders@example.com',
			password='OrderPass123!',
		)
		self.client.force_login(self.user)
		self.address = DeliveryAddress.objects.create(
			user=self.user,
			street='Main Street',
			number='10',
			postal_code='12345',
			phone_number='555-0000',
			delivery_zone='A',
			delivery_instructions='Ring bell',
		)
		self.product = Product.objects.create(
			category=Category.VEGETARIAN,
			name='Avocado Roll',
			description='Fresh avocado and rice',
			price=Decimal('9.50'),
			is_available=True,
			stock_quantity=100,
			spice_level=SpiceLevel.NONE,
		)

	def _create_order(self, status):
		return Order.objects.create(
			user=self.user,
			delivery_address=self.address,
			delivery_date='2030-01-01T12:00:00Z',
			allergens_notes='',
			status=status,
		)

	def test_pending_order_is_deleted(self):
		order = self._create_order(Order.OrderStatus.PENDING)

		response = self.client.post(reverse('orders:delete', args=[order.id_order]))

		self.assertRedirects(response, reverse('orders:list'))
		self.assertFalse(Order.objects.filter(pk=order.pk).exists())

	def test_confirmed_order_is_soft_cancelled(self):
		order = self._create_order(Order.OrderStatus.CONFIRMED)

		response = self.client.post(reverse('orders:delete', args=[order.id_order]))

		self.assertRedirects(response, reverse('orders:list'))
		order.refresh_from_db()
		self.assertEqual(order.status, Order.OrderStatus.CANCELLED)

	def test_delivered_order_cannot_be_cancelled(self):
		order = self._create_order(Order.OrderStatus.DELIVERED)

		response = self.client.post(reverse('orders:delete', args=[order.id_order]))

		self.assertRedirects(response, reverse('orders:detail', args=[order.id_order]))
		order.refresh_from_db()
		self.assertEqual(order.status, Order.OrderStatus.DELIVERED)


class CheckoutFormValidationTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='checkout@example.com',
			password='CheckoutPass123!',
		)
		self.address = DeliveryAddress.objects.create(
			user=self.user,
			street='Ocean Ave',
			number='12B',
			postal_code='90210',
			phone_number='555-1212',
			delivery_zone='B',
			delivery_instructions='Leave at door',
		)

	def test_rejects_past_delivery_date(self):
		form = CheckoutForm(
			data={
				'delivery_address': self.address.pk,
				'delivery_date': (timezone.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
				'allergens_notes': '',
			},
			user=self.user,
		)
		self.assertFalse(form.is_valid())
		self.assertIn('delivery_date', form.errors)

	def test_accepts_future_delivery_date(self):
		form = CheckoutForm(
			data={
				'delivery_address': self.address.pk,
				'delivery_date': (timezone.now() + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
				'allergens_notes': 'No peanuts',
			},
			user=self.user,
		)
		self.assertTrue(form.is_valid())


class OrdersQueryCountTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='perf@example.com',
			password='PerfPass123!',
		)
		self.client.force_login(self.user)

		self.address = DeliveryAddress.objects.create(
			user=self.user,
			street='Speed St',
			number='99',
			postal_code='10000',
			phone_number='555-8888',
			delivery_zone='Perf',
			delivery_instructions='',
		)

		self.products = []
		for i in range(3):
			self.products.append(
				Product.objects.create(
					category=Category.VEGETARIAN,
					name=f'Perf Roll {i}',
					description='Perf item',
					price=Decimal('10.00') + Decimal(i),
					is_available=True,
					stock_quantity=50,
					spice_level=SpiceLevel.NONE,
				)
			)

		self.cart = Cart.objects.create(user=self.user)
		for idx, product in enumerate(self.products, start=1):
			CartItem.objects.create(
				cart=self.cart,
				product=product,
				quantity=idx,
				product_name_snapshot=product.name,
				category_snapshot=product.category,
			)

		self.order = Order.objects.create(
			user=self.user,
			delivery_address=self.address,
			delivery_date='2030-01-01T12:00:00Z',
			allergens_notes='None',
			status=Order.OrderStatus.PENDING,
		)
		for idx, product in enumerate(self.products, start=1):
			OrderItem.objects.create(
				order=self.order,
				product=product,
				product_name=product.name,
				category=product.category,
				quantity=idx,
				unit_price=product.price,
			)
		self.order.calculate_total()

	def _assert_max_queries(self, url, max_queries):
		with CaptureQueriesContext(connection) as queries:
			response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(
			len(queries),
			max_queries,
			msg=f'Expected at most {max_queries} queries but got {len(queries)} for {url}',
		)

	def test_cart_view_query_budget(self):
		self._assert_max_queries(reverse('orders:cart'), max_queries=7)

	def test_order_detail_view_query_budget(self):
		self._assert_max_queries(
			reverse('orders:detail', args=[self.order.id_order]),
			max_queries=7,
		)

	def test_order_list_view_query_budget(self):
		self._assert_max_queries(reverse('orders:list'), max_queries=6)


class SuperuserOrderNotificationActionTests(TestCase):
	def setUp(self):
		self.superuser = CustomUser.objects.create_superuser(
			email='admin@example.com',
			password='AdminPass123!',
		)
		self.regular_user = CustomUser.objects.create_user(
			email='client@example.com',
			password='ClientPass123!',
		)
		self.address = DeliveryAddress.objects.create(
			user=self.regular_user,
			street='Admin Street',
			number='7',
			postal_code='77000',
			phone_number='555-7777',
			delivery_zone='North',
			delivery_instructions='',
		)
		self.order = Order.objects.create(
			user=self.regular_user,
			delivery_address=self.address,
			delivery_date='2030-01-01T12:00:00Z',
			allergens_notes='',
			status=Order.OrderStatus.PENDING,
		)

	def test_superuser_can_confirm_pending_order(self):
		self.client.force_login(self.superuser)
		response = self.client.post(
			reverse('orders:admin_confirm_received', args=[self.order.id_order]),
		)
		self.assertRedirects(response, reverse('products:list'))
		self.order.refresh_from_db()
		self.assertEqual(self.order.status, Order.OrderStatus.CONFIRMED)

	def test_non_staff_cannot_confirm_pending_order(self):
		self.client.force_login(self.regular_user)
		response = self.client.post(
			reverse('orders:admin_confirm_received', args=[self.order.id_order]),
		)
		self.assertEqual(response.status_code, 302)
		self.order.refresh_from_db()
		self.assertEqual(self.order.status, Order.OrderStatus.PENDING)

	def test_superuser_can_read_pending_count_json(self):
		self.client.force_login(self.superuser)
		response = self.client.get(reverse('orders:admin_pending_count'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['pending_count'], 1)

	def test_non_staff_cannot_read_pending_count_json(self):
		self.client.force_login(self.regular_user)
		response = self.client.get(reverse('orders:admin_pending_count'))
		self.assertEqual(response.status_code, 302)
