from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def test_jwt_auth(self):
        """Test JWT token obtain/refresh"""
        User.objects.create_user(username="testuser", password="testpass")

        auth_url = reverse("users:token_obtain_pair")
        response = self.client.post(
            auth_url, {"username": "testuser", "password": "testpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        refresh_url = reverse("users:token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": response.data["refresh"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
