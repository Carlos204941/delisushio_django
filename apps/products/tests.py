from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Product, Category, SpiceLevel


class ProductsQueryCountTests(TestCase):
	def setUp(self):
		for i in range(6):
			Product.objects.create(
				category=Category.VEGETARIAN if i % 2 == 0 else Category.POKE_BOWL,
				name=f'Product {i}',
				description='Menu item',
				price=Decimal('8.00') + Decimal(i),
				is_available=True,
				stock_quantity=100,
				spice_level=SpiceLevel.NONE,
			)

	def _assert_max_queries(self, url, max_queries):
		with CaptureQueriesContext(connection) as queries:
			response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(
			len(queries),
			max_queries,
			msg=f'Expected at most {max_queries} queries but got {len(queries)} for {url}',
		)

	def test_product_list_view_query_budget(self):
		self._assert_max_queries(reverse('products:list'), max_queries=5)

	def test_product_list_filtered_query_budget(self):
		self._assert_max_queries(f"{reverse('products:list')}?category=VEG", max_queries=5)


class ProductsSearchTests(TestCase):
	def setUp(self):
		Product.objects.create(
			category=Category.RAW_FISH,
			name='Salmon Nigiri',
			description='Fresh salmon',
			price=Decimal('12.00'),
			is_available=True,
			stock_quantity=20,
			spice_level=SpiceLevel.NONE,
		)
		Product.objects.create(
			category=Category.COOKED_FISH,
			name='Eel Nigiri',
			description='Smoked eel',
			price=Decimal('11.00'),
			is_available=True,
			stock_quantity=20,
			spice_level=SpiceLevel.NONE,
		)
		Product.objects.create(
			category=Category.VEGETARIAN,
			name='Avocado Roll',
			description='Classic vegetarian roll',
			price=Decimal('9.00'),
			is_available=True,
			stock_quantity=20,
			spice_level=SpiceLevel.NONE,
		)

	def test_search_by_name_filters_products(self):
		response = self.client.get(reverse('products:list'), {'q': 'nigiri'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Salmon Nigiri')
		self.assertContains(response, 'Eel Nigiri')
		self.assertNotContains(response, 'Avocado Roll')

	def test_search_and_category_filter_together(self):
		response = self.client.get(reverse('products:list'), {'q': 'nigiri', 'category': Category.RAW_FISH})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Salmon Nigiri')
		self.assertNotContains(response, 'Eel Nigiri')
		self.assertNotContains(response, 'Avocado Roll')
