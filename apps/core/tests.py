import os

from django.test import SimpleTestCase

from config.settings import env_bool, env_int, env_list


class SettingsEnvHelperTests(SimpleTestCase):
	def test_env_bool_handles_truthy_falsy_and_default(self):
		key = 'TEST_ENV_BOOL'

		os.environ.pop(key, None)
		self.assertTrue(env_bool(key, default=True))
		self.assertFalse(env_bool(key, default=False))

		os.environ[key] = 'true'
		self.assertTrue(env_bool(key, default=False))

		os.environ[key] = '0'
		self.assertFalse(env_bool(key, default=True))

	def test_env_int_parses_and_falls_back_to_default(self):
		key = 'TEST_ENV_INT'

		os.environ.pop(key, None)
		self.assertEqual(env_int(key, default=42), 42)

		os.environ[key] = '3600'
		self.assertEqual(env_int(key, default=0), 3600)

		os.environ[key] = 'invalid'
		self.assertEqual(env_int(key, default=7), 7)

	def test_env_list_splits_and_trims_values(self):
		key = 'TEST_ENV_LIST'

		os.environ.pop(key, None)
		self.assertEqual(env_list(key, default='a,b'), ['a', 'b'])

		os.environ[key] = ' one, two , ,three '
		self.assertEqual(env_list(key), ['one', 'two', 'three'])
