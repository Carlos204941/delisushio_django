from django.urls import reverse
from django.test import TestCase

from .models import CustomUser


class AuthenticationSecurityTests(TestCase):
	def setUp(self):
		self.password = 'SushiPass123!'
		self.user = CustomUser.objects.create_user(
			email='user@example.com',
			password=self.password,
			first_name='Test',
		)

	def test_login_rejects_external_next_url(self):
		response = self.client.post(
			reverse('authentication:login'),
			{
				'username': self.user.email,
				'password': self.password,
				'next': 'https://evil.example/phish',
			},
		)
		self.assertRedirects(response, reverse('products:list'))

	def test_login_allows_internal_next_url(self):
		target = reverse('orders:cart')
		response = self.client.post(
			reverse('authentication:login'),
			{
				'username': self.user.email,
				'password': self.password,
				'next': target,
			},
		)
		self.assertRedirects(response, target)

	def test_logout_requires_post_method(self):
		self.client.force_login(self.user)

		get_response = self.client.get(reverse('authentication:logout'))
		self.assertEqual(get_response.status_code, 405)
		self.assertIn('_auth_user_id', self.client.session)

		post_response = self.client.post(reverse('authentication:logout'))
		self.assertRedirects(post_response, reverse('products:list'))
		self.assertNotIn('_auth_user_id', self.client.session)
