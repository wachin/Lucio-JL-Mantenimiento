"""Utilidades compartidas de la aplicación."""

from __future__ import annotations


def _get_currency() -> str:
    """Obtener el código de moneda configurado (por defecto ``USD``)."""
    from luciotech.services.settings_service import SettingsService

    return SettingsService().get("currency", "USD").strip().upper() or "USD"


def currency_prefix() -> str:
    """Devolver el símbolo/prefijo de la moneda configurada.

    Para USD retorna ``$``; para cualquier otra moneda retorna el código
    seguido de un espacio (p. ej. ``EUR ``).
    """
    currency = _get_currency()
    return "$" if currency == "USD" else f"{currency} "


def format_money(value: float) -> str:
    """Formatear un valor monetario usando la moneda configurada.

    Lee el ajuste ``currency`` de la base de datos (por defecto ``USD``).
    Para USD usa el prefijo ``$``; para cualquier otra moneda usa el código
    seguido de un espacio (p. ej. ``EUR 1,234.56``).
    """
    return f"{currency_prefix()}{value:,.2f}"
