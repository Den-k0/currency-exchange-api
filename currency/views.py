from django.db import transaction
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from currency.models import CurrencyExchange, UserBalance
from currency.serializers import (
    CurrencyExchangeSerializer,
    UserBalanceSerializer,
)
from currency.utils import get_exchange_rate


@extend_schema(
    summary="Retrieve User Balance",
    description="Retrieve the balance of the authenticated user.",
    responses={200: UserBalanceSerializer},
)
class BalanceView(generics.RetrieveAPIView):
    serializer_class = UserBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(UserBalance, user=self.request.user)


@extend_schema(
    summary="Create Currency Exchange",
    description=(
        "This endpoint allows authenticated users to exchange their balance "
        "for a specified currency. It deducts 1 coin from the user's balance "
        "and records the exchange rate for the requested currency."
    ),
    request=CurrencyExchangeSerializer,
    parameters=[
        OpenApiParameter(
            name="currency_code",
            description="Currency code to exchange to (ISO 4217 format)",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[
                OpenApiExample("USD Example", value="USD"),
                OpenApiExample("EUR Example", value="EUR"),
            ],
        )
    ],
    responses={
        201: CurrencyExchangeSerializer,
        400: "Bad Request",
    },
    examples=[
        OpenApiExample(
            "Successful Request Example",
            value={"currency_code": "USD"},
            request_only=True,
            description="Example of a valid exchange request",
        ),
        OpenApiExample(
            "Successful Response Example",
            value={
                "id": 1,
                "user": 1,
                "currency_code": "USD",
                "rate": 1.0,
                "created_at": "2023-01-01T12:00:00Z",
            },
            response_only=True,
            status_codes=["201"],
            description="Example of successful exchange response",
        ),
        OpenApiExample(
            "Error Response Example",
            value={"error": "Invalid currency code"},
            response_only=True,
            status_codes=["400"],
            description="Example of error response for invalid currency",
        ),
    ],
)
class CurrencyExchangeView(generics.CreateAPIView):
    """
    API view to handle currency exchange requests.

    This view allows authenticated users to exchange their balance
    for a specified currency. It deducts 1 coin from the user's balance
    and records the exchange rate for the requested currency.

    Methods:
        create(request, *args, **kwargs): Handles the creation of a
                                          currency exchange record.
    """

    serializer_class = CurrencyExchangeSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Handle the creation of a currency exchange record.

        Args:
            request (Request): The request object containing
                               user and currency code.

        Returns:
            Response: A response object with the created
                      currency exchange data or an error message.
        """
        user = request.user
        currency_code = request.data.get("currency_code")

        if not currency_code:
            return Response(
                {"error": "currency_code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rate = get_exchange_rate(currency_code)
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        if rate is None:
            return Response(
                {"error": "Invalid currency code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_balance = UserBalance.objects.get(user=user)
        if user_balance.balance <= 0:
            return Response(
                {"error": "Insufficient balance"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_balance.balance -= 1
        user_balance.save()

        exchange = CurrencyExchange.objects.create(
            user=user, currency_code=currency_code.upper(), rate=rate
        )

        return Response(
            CurrencyExchangeSerializer(exchange).data,
            status=status.HTTP_201_CREATED,
        )


class CurrencyExchangeFilter(filters.FilterSet):
    """
    FilterSet for filtering CurrencyExchange records.

    This filter allows users to filter currency exchange records
    based on the currency code and date range.

    Attributes:
        currency_code (CharFilter): Filter to match
                                    the exact currency code.
        start_date (DateFilter): Filter for records
                                 created on or after this date.
        end_date (DateFilter): Filter for records
                               created on or before this date.

    Meta:
        model (CurrencyExchange): The model to filter.
        fields (list): A list of fields to filter by.

    Example:
        To filter records with currency code 'USD'
        and date range from '2023-01-01' to '2023-12-31':
            ```
            /api/currency/history/?currency_code=USD
            &start_date=2025-01-01&end_date=2025-12-31
            ```
    """

    currency_code = filters.CharFilter(
        field_name="currency_code", lookup_expr="iexact"
    )
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = CurrencyExchange
        fields = ["currency_code", "created_at"]

    def filter_queryset(self, queryset):
        cleaned_data = self.form.cleaned_data
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date")

        return super().filter_queryset(queryset)


@extend_schema(
    summary="Get currency exchange history",
    description=(
        "Returns paginated history of currency exchanges"
        "for authenticated user. Supports filtering"
        "by currency code and date range."
    ),
    parameters=[
        OpenApiParameter(
            name="currency_code",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by currency code (e.g. USD, EUR)",
            examples=[
                OpenApiExample("USD example", value="USD"),
                OpenApiExample("EUR example", value="EUR"),
            ],
        ),
        OpenApiParameter(
            name="start_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Start date for filtering (YYYY-MM-DD)",
            examples=[
                OpenApiExample("Start date example", value="2025-01-01"),
            ],
        ),
        OpenApiParameter(
            name="end_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="End date for filtering (YYYY-MM-DD)",
            examples=[
                OpenApiExample("End date example", value="2025-12-31"),
            ],
        ),
    ],
    examples=[
        OpenApiExample(
            "Successful response",
            value={
                "count": 10,
                "next": "http://api.example.com/currency/history/?page=2",
                "previous": None,
                "results": [
                    {
                        "currency_code": "USD",
                        "rate": 1,
                        "created_at": "2025-03-25T12:34:56Z",
                    }
                ],
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Invalid date range",
            value={"detail": "End date must be after start date"},
            response_only=True,
            status_codes=["400"],
        ),
    ],
    responses={
        200: CurrencyExchangeSerializer(many=True),
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
)
class CurrencyExchangeHistoryView(generics.ListAPIView):
    """
    API view to list currency exchange history for the authenticated user.

    This view allows authenticated users to retrieve their currency
    exchange history, filtered by currency code and date range.

    Methods:
        get_queryset(): Returns the queryset of currency exchange records
                        for the authenticated user, ordered by
                        creation date in descending order.
    """

    serializer_class = CurrencyExchangeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CurrencyExchangeFilter
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        return CurrencyExchange.objects.filter(
            user=self.request.user
        ).order_by("-created_at")
