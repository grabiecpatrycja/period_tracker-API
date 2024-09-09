from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User


class RegistrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        data = {'username': 'name', 'email': 'name@email.com', 'password': 'password'}
        url = reverse('register')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_wrong_email(self):
        User.objects.create(first_name='name_1', email='name@email.com', password='password1')
        data = {'first_name': 'name_2', 'email': 'name@email.com', 'password': 'password2'}
        url = reverse('register')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)