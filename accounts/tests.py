from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User

class AccountsTests(APITestCase):
    def test_registration(self):
        url = reverse('register')
        data = {
            'email': 'maxsatul2007@gmail.com',
            'password': 'strong_password_123',
            'username': 'testuser'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='maxsatul2007@gmail.com').exists())
