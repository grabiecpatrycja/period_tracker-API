from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import date
from tracker.models import Period
from freezegun import freeze_time


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

class PeriodTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.otheruser = User.objects.create_user(username='otheruser', password='otherpassword')
        self.client.force_authenticate(user=self.user)

    def test_no_authentication(self):
        self.client.force_authenticate(user=None)
        url = reverse('period-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_object(self):
        date_1 = date(1989, 2, 24)
        date_2 = date(1989, 3, 10)
        data = {'first_day': date_1, 'ovulation_day': date_2}
        url = reverse('period-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Period.objects.count(), 1)

    def test_create_wrong_date(self):
        date_1 = date(1989, 3, 10)
        date_2 = date(1989, 2, 24)
        data = {'first_day': date_1, 'ovulation_day': date_2}
        url = reverse('period-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_firstday(self):
        date_1 = date(1989, 2, 24)
        data = {'first_day': date_1}
        url = reverse('period-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Period.objects.count(), 1)

    def test_add_ovulationday(self):
        last_period = Period.objects.create(first_day='1989-02-24', user=self.user)
        date_2 = date(1989, 3, 10)
        data = {'ovulation_day': date_2}
        url = reverse('period-detail', args=[last_period.id])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        last_period.refresh_from_db()
        self.assertEqual(Period.objects.count(), 1)
        self.assertEqual(response.data['ovulation_day'], '1989-03-10')

    def test_add_wrong_ovulationday(self):
        last_period = Period.objects.create(first_day='1989-02-24', user=self.user)
        date_2 = date(1989, 1, 10)
        data = {'ovulation_day': date_2}
        url = reverse('period-detail', args=[last_period.id])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_objects(self):
        Period.objects.create(first_day='2024-01-01', ovulation_day='2024-01-15', user=self.user)
        Period.objects.create(first_day='2024-01-30', ovulation_day='2024-02-14', user=self.user)
        Period.objects.create(first_day='2024-01-03', ovulation_day='2024-01-19', user=self.otheruser)
        url = reverse('period-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queryset_list = response.json()
        self.assertEqual(len(queryset_list), 2)
        for item in queryset_list:
            period = Period.objects.get(id=item['id'])
            self.assertEqual(period.user, self.user)

    def test_get_single_object(self):
        period_1 = Period.objects.create(first_day='2024-01-01', ovulation_day='2024-01-15', user=self.user)
        period_2 = Period.objects.create(first_day='2024-01-30', ovulation_day='2024-02-14', user=self.user)
        url = reverse('period-detail', args=[period_2.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_day'], '2024-01-30')
        self.assertEqual(response.data['length'], 29)
        self.assertEqual(response.data['ovul_len'], 16)

    def test_delete_object(self):
        period = Period.objects.create(first_day='2024-01-01', ovulation_day='2024-01-15', user=self.user)
        Period.objects.create(first_day='2024-01-03', ovulation_day='2024-01-19', user=self.otheruser)
        url = reverse('period-detail', args=[period.id])
        response = self.client.delete(url,format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Period.objects.count(), 1)
        with self.assertRaises(Period.DoesNotExist):
            period.refresh_from_db()

    def test_last(self):
        Period.objects.create(first_day='2024-01-01', ovulation_day='2024-01-15', user=self.user)
        Period.objects.create(first_day='2024-01-30', ovulation_day='2024-02-14', user=self.user)
        Period.objects.create(first_day='2024-02-28', user=self.user)
        url = reverse('period-last')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_day'], '2024-02-28')

@freeze_time("2024-10-08")
class StatisticTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def test_no_authentication(self):
        self.client.force_authenticate(user=None)
        url = reverse('period-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_statistic(self):
        Period.objects.create(first_day = '2024-08-02', ovulation_day = '2024-08-15', user=self.user)
        Period.objects.create(first_day = '2024-09-02', ovulation_day = '2024-09-16', user=self.user)
        Period.objects.create(first_day = '2024-10-01', user=self.user)

        url = reverse('statistic')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queryset_list = response.json()
        self.assertEqual(queryset_list,{'averages': {'avg_length': 30, 
                                                    'avg_ovulation': 14},
                                        'predictions': {'day': 8, 
                                                        'next_period': '2024-10-31', 
                                                        'days_to_next': 23,
                                                        'next_ovulation': '2024-10-15', 
                                                        'days_to_ovul': 7}})
        
    def test_after_ovulation(self):
        Period.objects.create(first_day = '2024-07-23', ovulation_day = '2024-08-05', user=self.user)
        Period.objects.create(first_day = '2024-08-22', ovulation_day = '2024-09-06', user=self.user)
        Period.objects.create(first_day = '2024-09-20', ovulation_day = '2024-10-04', user=self.user)

        url = reverse('statistic')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queryset_list = response.json()
        self.assertEqual(queryset_list,{'averages': {'avg_length': 30, 
                                                    'avg_ovulation': 15},
                                        'predictions': {'day': 19, 
                                                        'next_period': '2024-10-20', 
                                                        'days_to_next': 12,
                                                        'next_ovulation': None, 
                                                        'days_to_ovul': None}})
        
    def test_no_ovulation_data(self):
        Period.objects.create(first_day = '2024-08-02', user=self.user)
        Period.objects.create(first_day = '2024-09-02', user=self.user)
        Period.objects.create(first_day = '2024-10-01', user=self.user)
        url = reverse('statistic')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queryset_list = response.json()
        self.assertEqual(queryset_list,{'averages': {'avg_length': 30, 
                                                    'avg_ovulation': 14},
                                        'predictions': {'day': 8, 
                                                        'next_period': '2024-10-31', 
                                                        'days_to_next': 23,
                                                        'next_ovulation': '2024-10-15', 
                                                        'days_to_ovul': 7}})
        
    def test_late_cycle(self):
        Period.objects.create(first_day = '2024-07-23', ovulation_day = '2024-08-05', user=self.user)
        Period.objects.create(first_day = '2024-08-22', user=self.user)
        url = reverse('statistic')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queryset_list = response.json()
        self.assertEqual(queryset_list,{'averages': {'avg_length': 30, 
                                                    'avg_ovulation': 14},
                                        'predictions': {'day': 48, 
                                                        'next_period': '2024-09-21', 
                                                        'days_to_next': -17,
                                                        'next_ovulation': '2024-09-05', 
                                                        'days_to_ovul': None}})
        
    def test_no_data(self):
        Period.objects.create(first_day = '2024-10-01', user=self.user)
        url = reverse('statistic')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'message': 'Add more data to perform calculations.'})