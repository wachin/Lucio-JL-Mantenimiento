"""Utilidades compartidas de la aplicación."""

from __future__ import annotations


def _get_currency() -> str:
    """Obtener el código de moneda configurado (por defecto ``USD``)."""
    from luciotech.services.settings_service import SettingsService

    return SettingsService().get("currency", "USD").strip().upper() or "USD"


def currency_prefix() -> str:
    """Devolver el símbolo o código de la moneda configurada."""
    currency = _get_currency()
    return "$" if currency == "USD" else f"{currency} "


def format_money(value: float) -> str:
    """Formatear un valor monetario usando la moneda configurada."""
    return f"{currency_prefix()}{value:,.2f}"
