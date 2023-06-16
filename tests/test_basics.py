import pytest
from flask import current_app
from krom_app import create_app
'''
class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['MZK_IP'])'''

class TestApp:

    def test_app_exists(self):
        assert current_app

    def test_app_has_valid_ip(self):
        valid_ips = ['10.2.0.8', '10.223.1.8']
        assert current_app.config['MZK_IP'] in valid_ips 
        