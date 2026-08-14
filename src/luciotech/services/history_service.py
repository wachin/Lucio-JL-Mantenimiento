"""Consulta unificada de la actividad registrada en las órdenes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from luciotech.database.connection import get_session
from luciotech.database.repositories import HistoryEventRepo, StatusHistoryRepo


@dataclass(frozen=True)
class ActivityRecord:
    """Fila normalizada para el historial global."""

    timestamp: datetime
    category: str
    order_id: int
    order_number: str
    customer_name: str
    equipment: str
    detail: str
    user: str


class HistoryService:
    """Combinar cambios de estado y eventos de todas las órdenes."""

    def __init__(self) -> None:
        self.session = get_session()
        self.status_repo = StatusHistoryRepo(self.session)
        self.event_repo = HistoryEventRepo(self.session)

    def get_activity(
        self,
        query: str = "",
        category: str = "Todos",
        limit: int = 500,
    ) -> list[ActivityRecord]:
        """Obtener actividad reciente aplicando filtros de texto y categoría."""
        self.session.expire_all()
        records: list[ActivityRecord] = []

        if category in ("Todos", "Cambios de estado"):
            for status in self.status_repo.get_recent(limit):
                order = status.order
                previous = status.previous_status.strip()
                if previous:
                    detail = f"{previous} → {status.new_status}"
                else:
                    detail = f"Orden creada: {status.new_status}"
                if status.comment:
                    detail = f"{detail} — {status.comment}"
                records.append(
                    self._record(
                        status.changed_at,
                        "Cambio de estado",
                        order,
                        detail,
                        status.user or "",
                    )
                )

        if category not in ("Cambios de estado",):
            for event in self.event_repo.get_recent(limit):
                if category not in ("Todos", "Eventos") and event.event_type != category:
                    continue
                detail = event.title
                if event.description:
                    detail = f"{detail} — {event.description}"
                records.append(
                    self._record(
                        event.created_at,
                        event.event_type,
                        event.order,
                        detail,
                        event.user or "",
                    )
                )

        if query.strip():
            needle = query.strip().casefold()
            records = [record for record in records if self._matches(record, needle)]

        records.sort(key=lambda record: record.timestamp, reverse=True)
        return records[:limit]

    @staticmethod
    def _record(timestamp, category, order, detail, user) -> ActivityRecord:
        equipment = order.equipment
        equipment_name = ""
        if equipment:
            equipment_name = " ".join(
                part
                for part in (
                    equipment.equipment_type,
                    equipment.brand or "",
                    equipment.model or "",
                )
                if part
            )
        return ActivityRecord(
            timestamp=timestamp,
            category=category,
            order_id=order.id,
            order_number=order.order_number,
            customer_name=order.customer.full_name if order.customer else "",
            equipment=equipment_name,
            detail=detail,
            user=user,
        )

    @staticmethod
    def _matches(record: ActivityRecord, needle: str) -> bool:
        values = (
            record.category,
            record.order_number,
            record.customer_name,
            record.equipment,
            record.detail,
            record.user,
        )
        return any(needle in value.casefold() for value in values)
