from django.urls import path

from currency.views import (
    BalanceView, CurrencyExchangeView, CurrencyExchangeHistoryView
)

urlpatterns = [
    path("balance/", BalanceView.as_view(), name="balance"),
    path("", CurrencyExchangeView.as_view(), name="currency"),
    path(
        "history/",
        CurrencyExchangeHistoryView.as_view(),
        name="currency_history"
    ),
]

app_name = "currency"
