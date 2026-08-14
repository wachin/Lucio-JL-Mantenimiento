"""Acceso tipado a la configuración persistente de la aplicación."""

from __future__ import annotations

import json
from datetime import datetime

from luciotech.config import DEFAULT_ORDER_FORMAT, EQUIPMENT_TYPES
from luciotech.database.connection import get_session
from luciotech.database.models import Settings


class SettingsService:
    """Leer configuraciones con valores predeterminados seguros."""

    def __init__(self) -> None:
        self.session = get_session()

    def get(self, key: str, default: str = "") -> str:
        setting = self.session.query(Settings).filter(Settings.key == key).first()
        return setting.value if setting and setting.value is not None else default

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.get(key, str(default)))
        except (TypeError, ValueError):
            return default

    def get_equipment_types(self) -> list[str]:
        raw_value = self.get("equipment_types", "")
        if raw_value:
            try:
                values = json.loads(raw_value)
                if isinstance(values, list):
                    cleaned = list(
                        dict.fromkeys(str(value).strip() for value in values if str(value).strip())
                    )
                    if cleaned:
                        return cleaned
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        return list(EQUIPMENT_TYPES)

    def get_order_format(self) -> str:
        template = self.get("order_format", DEFAULT_ORDER_FORMAT).strip()
        try:
            self.format_order_number(template, datetime.now(), 1)
        except ValueError:
            return DEFAULT_ORDER_FORMAT
        return template

    @staticmethod
    def format_order_number(template: str, when: datetime, sequence: int) -> str:
        """Aplicar y validar una plantilla de número de orden."""
        if "{sequence" not in template:
            raise ValueError("El formato debe incluir el campo {sequence}")
        try:
            result = template.format(
                year=when.year,
                month=when.month,
                day=when.day,
                sequence=sequence,
            ).strip()
        except (KeyError, IndexError, ValueError) as error:
            raise ValueError(f"Formato de orden no válido: {error}") from error
        if not result:
            raise ValueError("El formato de orden no puede quedar vacío")
        if len(result) > 30:
            raise ValueError("El número de orden generado no puede superar 30 caracteres")
        return result
