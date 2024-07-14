import unittest
from unittest.mock import MagicMock, patch
from app import app
from faker import Faker


fake = Faker()

class TestTokenEndpoint(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    @patch('app.routes.encode_token')
    @patch('app.routes.db.session.scalars')
    @patch('app.routes.check_password_hash')
    def test_successful_authenticate(self, mock_check_hash, mock_scalars, mock_encode_token):
        mock_user = MagicMock()
        mock_user.id = 123
        mock_query = MagicMock()
        mock_query.first.return_value = mock_user
        mock_scalars.return_value = mock_query
        mock_check_hash.return_value = True
        mock_encode_token.return_value = 'random.jwt.token'

        request_body = {
            "username": fake.user_name(),
            "password": fake.password()
        }

        response = self.client.post('/token', json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['token'], 'random.jwt.token')


    def test_unauthorized_user(self):
        request_body = {
            "username": fake.user_name(),
            "password": fake.password()
        }

        response = self.client.post('/token', json=request_body)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], "Username and/or password is incorrect")