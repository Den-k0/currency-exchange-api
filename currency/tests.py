from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from currency.models import CurrencyExchange, UserBalance

User = get_user_model()


class CurrencyExchangeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)
        UserBalance.objects.create(user=self.user, balance=1000)
        self.url = reverse("currency:currency")

    def test_successful_exchange(self):
        """Test successful currency exchange"""
        response = self.client.post(self.url, {"currency_code": "EUR"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CurrencyExchange.objects.exists())
        self.assertEqual(UserBalance.objects.get(user=self.user).balance, 999)

    def test_insufficient_balance(self):
        """Test exchange with zero balance"""
        UserBalance.objects.filter(user=self.user).update(balance=0)
        response = self.client.post(self.url, {"currency_code": "EUR"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient balance", str(response.data))

    def test_invalid_currency(self):
        """Test with invalid currency code"""
        response = self.client.post(self.url, {"currency_code": "INVALID"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid currency code", str(response.data))

    def test_api_timeout(self):
        """Test handling of ExchangeRate API timeout"""
        with patch("currency.views.get_exchange_rate") as mock_get_rate:
            mock_get_rate.side_effect = ValueError("Exchange rate API timeout")
            response = self.client.post(self.url, {"currency_code": "EUR"})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Exchange rate API timeout", str(response.data))


class HistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)
        CurrencyExchange.objects.create(
            user=self.user, currency_code="USD", rate=1.0
        )
        self.url = reverse("currency:currency_history")

    def test_history_filtering(self):
        """Test filtering by currency and date"""
        response = self.client.get(f"{self.url}?currency_code=USD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_empty_history(self):
        """Test empty history response"""
        CurrencyExchange.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 0)
        else:
            self.assertEqual(len(response.data), 0)

    def test_date_filter_validation(self):
        """Test invalid date range"""
        response = self.client.get(
            f"{self.url}?start_date=2025-01-02&end_date=2025-01-01"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BalanceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("currency:balance")

    def test_balance_retrieval(self):
        """Test balance retrieval"""
        UserBalance.objects.create(user=self.user, balance=500)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["balance"], 500)

    def test_no_balance_record(self):
        """Test when balance record doesn't exist"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
