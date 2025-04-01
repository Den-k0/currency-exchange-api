import requests

from core.settings import api_key

EXCHANGE_RATE_API_URL = (
    f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
)


def get_exchange_rate(currency_code: str) -> float | None:
    """
    Fetch the exchange rate for a given currency code.

    Args:
        currency_code (str): The currency code for which
                             to fetch the exchange rate.

    Returns:
        float: The exchange rate for the specified currency code,
               or None if the currency code is not found.

    Raises:
        ValueError: If the ExchangeRate API key is not configured,
                    if there is an error fetching the exchange rates,
                    or if the request times out.
    """
    if not api_key:
        raise ValueError("ExchangeRate API key not configured")

    try:
        response = requests.get(EXCHANGE_RATE_API_URL, timeout=5)
        data = response.json()

        if response.status_code != 200 or "conversion_rates" not in data:
            raise ValueError("Error fetching exchange rates")

        return data["conversion_rates"].get(currency_code.upper(), None)
    except requests.Timeout:
        raise ValueError("Exchange rate API timeout")
