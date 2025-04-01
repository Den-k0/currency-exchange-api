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

    @patch("currency.views.get_exchange_rate")
    def test_successful_exchange(self, mock_get_rate):
        """Test successful currency exchange"""
        mock_get_rate.return_value = 1
        response = self.client.post(
            self.url, {"currency_code": "USD"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CurrencyExchange.objects.exists())
        self.assertEqual(UserBalance.objects.get(user=self.user).balance, 999)

    @patch("currency.views.get_exchange_rate")
    def test_insufficient_balance(self, mock_get_rate):
        """Test exchange with zero balance"""
        mock_get_rate.return_value = 1.0
        UserBalance.objects.filter(user=self.user).update(balance=0)
        response = self.client.post(
            self.url, {"currency_code": "USD"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Insufficient balance")

    @patch("currency.views.get_exchange_rate")
    def test_invalid_currency(self, mock_get_rate):
        """Test with invalid currency code"""
        mock_get_rate.return_value = None
        response = self.client.post(
            self.url, {"currency_code": "INVALID"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid currency code")

    @patch("currency.views.get_exchange_rate")
    def test_api_timeout(self, mock_get_rate):
        """Test handling of ExchangeRate API timeout"""
        mock_get_rate.side_effect = ValueError("Exchange rate API timeout")
        response = self.client.post(
            self.url, {"currency_code": "EUR"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Exchange rate API timeout")

    def test_missing_currency_code(self):
        """Test request without currency_code parameter"""
        response = self.client.post(self.url,{}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "currency_code is required")


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
