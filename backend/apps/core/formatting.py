"""Central place for locale-specific display formats. Screens and the API call these instead of formatting by hand."""


def money(amount: int) -> str:
    """Chilean pesos have no decimals: 30000 -> '$30.000'."""
    return "$" + f"{int(amount):,}".replace(",", ".")
