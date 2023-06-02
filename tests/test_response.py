import unittest
import requests
from flask import current_app
from krom_app import create_app


class ResponseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
    
    def tearDown(self):
        self.app_context.pop()

    def test_home_page(self):
        response = requests.get('http://localhost:5000/home')
        self.assertEqual(response.status_code, 200)
    
    def test_processes_page(self):
        response = requests.get('http://localhost:5000/processes')
        self.assertEqual(response.status_code, 200)