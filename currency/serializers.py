from django.core.validators import RegexValidator
from rest_framework import serializers
from currency.models import UserBalance, CurrencyExchange


class CurrencyExchangeSerializer(serializers.ModelSerializer):
    """
    Serializer for the CurrencyExchange model,
    providing read-only access to the exchange rate.
    """

    rate = serializers.FloatField(read_only=True)
    currency_code = serializers.CharField(
        max_length=3,
        min_length=3,
        validators=[RegexValidator(regex="^[A-Z]{3}$")],
    )

    class Meta:
        model = CurrencyExchange
        fields = ("currency_code", "rate", "created_at")


class UserBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserBalance model,
    providing access to the user's balance.
    """

    class Meta:
        model = UserBalance
        fields = ("user", "balance")
