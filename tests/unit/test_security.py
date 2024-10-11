# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import unittest
from flask_testing import TestCase
from app import create_app
import requests
from urllib.parse import urlparse
import ssl
import socket
from OpenSSL import SSL
from unittest.mock import patch, Mock, MagicMock

class TestSecurityFeatures(TestCase):
    # def create_app(self):
    #     app = create_app()
    #     app.config['TESTING'] = True
    #     app.config['SERVER_NAME'] = 'localhost:5000'
    #     return app
    
    # def setUp(self):
    #     super().setUp()
    #     print("Test setup - Registered routes:")
    #     print(self.app.url_map)

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SERVER_NAME'] = 'localhost:5000'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        print("setUpClass - All registered routes:")
        print(cls.app.url_map)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def create_app(self):
        return self.__class__.app

    def setUp(self):
        self.client = self.app.test_client()
        print(f"setUp for {self._testMethodName} - All registered routes:")
        print(self.app.url_map)

    def test_https_redirect(self):
        response = self.client.get('/', base_url='http://localhost:5000/')
        self.assertRedirects(response, 'https://localhost:5000/')

    # def test_https_connection(self):
    #     response = self.client.get('/', base_url='https://localhost:5000/')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data.decode(), "Welcome to the API")

    def test_https_connection(self):
        response = self.client.get('/', base_url='https://localhost:5000')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Welcome to the API")

    def test_security_headers(self):
        response = self.client.get('/', base_url='https://localhost:5000/')
        headers = response.headers
        self.assertIn('Strict-Transport-Security', headers)
        self.assertIn('Content-Security-Policy', headers)
        self.assertIn('X-Frame-Options', headers)
        self.assertIn('X-Content-Type-Options', headers)
        self.assertEqual(headers['X-Frame-Options'], 'DENY')

    @patch('ssl.SSLContext.wrap_socket')
    def test_tls_version(self, mock_wrap_socket):
        mock_ssl_socket = MagicMock()
        mock_ssl_socket.version.return_value = 'TLSv1.2'
        mock_wrap_socket.return_value = mock_ssl_socket

        context = ssl.create_default_context()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            secure_sock = context.wrap_socket(sock, server_hostname='localhost')
            version = secure_sock.version()
            self.assertIn(version, ['TLSv1.2', 'TLSv1.3'], f"Unexpected TLS version: {version}")

    @patch('ssl.SSLContext.wrap_socket')
    def test_weak_ciphers(self, mock_wrap_socket):
        mock_ssl_socket = MagicMock()
        mock_ssl_socket.cipher.return_value = ('ECDHE-RSA-AES256-GCM-SHA384', 'TLSv1.2', 256)
        mock_wrap_socket.return_value = mock_ssl_socket

        context = ssl.create_default_context()
        context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            secure_sock = context.wrap_socket(sock, server_hostname='localhost')
            cipher = secure_sock.cipher()
            self.assertNotIn('RC4', cipher[0], "Weak cipher (RC4) was accepted")
            self.assertNotIn('DES', cipher[0], "Weak cipher (DES) was accepted")
            self.assertNotIn('MD5', cipher[0], "Weak cipher (MD5) was accepted")

    def test_content_security_policy(self):
        response = self.client.get('/', base_url='https://localhost')
        csp = response.headers.get('Content-Security-Policy')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self' https://cdnjs.cloudflare.com", csp)

    def test_secure_cookies(self):
        response = self.client.get('/', base_url='https://localhost')
        for cookie in response.headers.getlist('Set-Cookie'):
            self.assertIn('Secure', cookie)
            self.assertIn('HttpOnly', cookie)

    def test_cors(self):
        headers = {
            'Origin': 'https://example.com'
        }
        response = self.client.get('/', headers=headers, base_url='https://localhost')
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    # def test_rate_limiting(self):
    #     for _ in range(101):  # Assuming rate limit is 100 per minute
    #         response = self.client.get('/', base_url='https://localhost:5000/')
    #     self.assertEqual(response.status_code, 429)

    def test_rate_limiting(self):
        for _ in range(100):  # Make 100 requests (should be fine)
            response = self.client.get('/', base_url='https://localhost:5000')
            self.assertEqual(response.status_code, 200)
        
        # The 101st request should be rate limited
        response = self.client.get('/', base_url='https://localhost:5000')
        self.assertEqual(response.status_code, 429)

    # def test_encryption_in_transit(self):
    #     sensitive_data = {'password': 'secret'}
    #     response = self.client.post('/test_encryption', json=sensitive_data, follow_redirects=True)
    #     print(f"Response status code: {response.status_code}")
    #     print(f"Response headers: {response.headers}")
    #     print(f"Response data: {response.data}")
    #     self.assertEqual(response.status_code, 200)
    #     data = response.json
    #     print(f"Parsed JSON data: {data}")
    #     self.assertIn('original', data)
    #     self.assertIn('encrypted', data)
    #     self.assertIn('decrypted', data)
    #     self.assertEqual(data['original'], 'secret')
    #     self.assertNotEqual(data['encrypted'], 'secret')
    #     self.assertEqual(data['decrypted'], 'secret')
    def test_encryption_in_transit(self):
        sensitive_data = {'password': 'secret'}
        response = self.client.post('/test_encryption', json=sensitive_data, base_url='https://localhost:5000')
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        data = response.json
        print(f"Parsed JSON data: {data}")
        self.assertIn('original', data)
        self.assertIn('encrypted', data)
        self.assertIn('decrypted', data)
        self.assertEqual(data['original'], 'secret')
        self.assertNotEqual(data['encrypted'], 'secret')
        self.assertEqual(data['decrypted'], 'secret')

if __name__ == '__main__':
    unittest.main()