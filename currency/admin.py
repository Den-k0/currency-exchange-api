from django.contrib import admin

from currency.models import CurrencyExchange, UserBalance

admin.site.register(CurrencyExchange)
admin.site.register(UserBalance)
