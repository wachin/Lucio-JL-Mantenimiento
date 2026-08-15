"""Panel de inicio con indicadores operativos del taller."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from luciotech.config import ORDER_STATUSES
from luciotech.database.models import Payment, ServiceOrder
from luciotech.services.order_service import OrderService
from luciotech.utils import format_money


FINAL_STATUSES = {"Entregado", "Cancelado", "No reparable"}


class HomePage(QWidget):
    """Resumen actualizado de la carga de trabajo del taller."""

    order_opened = pyqtSignal(int)
    new_reception_requested = pyqtSignal()
    orders_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = OrderService()
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        heading = QHBoxLayout()
        title = QLabel("Inicio")
        title.setStyleSheet("font-size: 26px; font-weight: bold; padding: 12px 0;")
        heading.addWidget(title)
        heading.addStretch()

        new_button = QPushButton("Nueva recepción")
        new_button.clicked.connect(self.new_reception_requested.emit)
        heading.addWidget(new_button)
        orders_button = QPushButton("Ver todas las órdenes")
        orders_button.clicked.connect(self.orders_requested.emit)
        heading.addWidget(orders_button)
        refresh_button = QPushButton("Actualizar")
        refresh_button.clicked.connect(self.refresh)
        heading.addWidget(refresh_button)
        layout.addLayout(heading)

        cards = QGridLayout()
        self._active_value = self._add_card(cards, 0, "Órdenes activas", "0", "#2563eb")
        self._ready_value = self._add_card(cards, 1, "Listas para entregar", "0", "#16a34a")
        self._overdue_value = self._add_card(cards, 2, "Órdenes retrasadas", "0", "#dc2626")
        self._balance_value = self._add_card(cards, 3, "Saldo pendiente", "$0.00", "#d97706")
        self._received_today_value = self._add_card(cards, 4, "Equipos recibidos hoy", "0", "#0891b2")
        self._delivered_month_value = self._add_card(cards, 5, "Equipos entregados este mes", "0", "#7c3aed")
        self._month_income_value = self._add_card(cards, 6, "Ingresos del mes", "$0.00", "#059669")
        self._upcoming_deliveries_value = self._add_card(cards, 7, "Entregas próximas", "0", "#e11d48")
        layout.addLayout(cards)

        content = QHBoxLayout()

        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        status_title = QLabel("Resumen por estado")
        status_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(status_title)
        self._status_table = QTableWidget()
        self._status_table.setColumnCount(2)
        self._status_table.setHorizontalHeaderLabels(["Estado", "Cantidad"])
        self._status_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._status_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._status_table.verticalHeader().hide()
        self._status_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._status_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        status_layout.addWidget(self._status_table)
        content.addWidget(status_frame, 1)

        recent_frame = QFrame()
        recent_frame.setFrameShape(QFrame.Shape.StyledPanel)
        recent_layout = QVBoxLayout(recent_frame)
        recent_title = QLabel("Órdenes recientes")
        recent_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        recent_layout.addWidget(recent_title)
        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(6)
        self._recent_table.setHorizontalHeaderLabels(
            ["Nº Orden", "Fecha", "Cliente", "Equipo", "Estado", "Saldo"]
        )
        self._recent_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._recent_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._recent_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._recent_table.setAlternatingRowColors(True)
        self._recent_table.verticalHeader().hide()
        self._recent_table.cellDoubleClicked.connect(self._open_recent_order)
        recent_header = self._recent_table.horizontalHeader()
        recent_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        recent_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        recent_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        recent_layout.addWidget(self._recent_table)
        hint = QLabel("Doble clic sobre una fila para abrir la orden")
        hint.setStyleSheet("color: palette(mid); font-size: 11px;")
        recent_layout.addWidget(hint)
        content.addWidget(recent_frame, 3)

        layout.addLayout(content, 1)
        self._updated_label = QLabel()
        self._updated_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._updated_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        layout.addWidget(self._updated_label)

    @staticmethod
    def _add_card(
        layout: QGridLayout,
        column: int,
        title: str,
        initial_value: str,
        color: str,
    ) -> QLabel:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            f"QFrame {{ border-left: 5px solid {color}; border-radius: 6px; }}"
        )
        card_layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; color: palette(mid);")
        value_label = QLabel(initial_value)
        value_label.setStyleSheet("font-size: 25px; font-weight: bold;")
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        layout.addWidget(card, 0, column)
        return value_label

    def refresh(self, *_args) -> None:
        self._service.session.expire_all()
        orders = list(self._service.get_all())
        now = datetime.now()
        active = [order for order in orders if order.status not in FINAL_STATUSES]
        ready = [order for order in orders if order.status == "Listo para entregar"]
        overdue = [
            order
            for order in active
            if order.estimated_delivery_date and order.estimated_delivery_date < now
        ]
        balance = sum(max(order.balance, 0.0) for order in orders)

        self._active_value.setText(str(len(active)))
        self._ready_value.setText(str(len(ready)))
        self._overdue_value.setText(str(len(overdue)))
        self._balance_value.setText(format_money(balance))

        # New indicators
        today = now.date()
        received_today = [
            order for order in orders
            if order.intake_date and order.intake_date.date() == today
        ]
        self._received_today_value.setText(str(len(received_today)))

        month_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            month_end = datetime(now.year + 1, 1, 1)
        else:
            month_end = datetime(now.year, now.month + 1, 1)

        delivered_this_month = [
            order for order in orders
            if order.delivery_date and month_start <= order.delivery_date < month_end
        ]
        self._delivered_month_value.setText(str(len(delivered_this_month)))

        month_income = sum(
            payment.amount
            for order in orders
            for payment in order.payments
            if month_start <= payment.payment_date < month_end
        )
        self._month_income_value.setText(format_money(month_income))

        upcoming_deadline = now + timedelta(days=7)
        upcoming_deliveries = [
            order for order in active
            if order.estimated_delivery_date and now <= order.estimated_delivery_date <= upcoming_deadline
        ]
        self._upcoming_deliveries_value.setText(str(len(upcoming_deliveries)))

        self._populate_statuses(orders)
        self._populate_recent(orders[:10])
        self._updated_label.setText(f"Actualizado: {now:%Y-%m-%d %H:%M:%S}")

    def _populate_statuses(self, orders: list[ServiceOrder]) -> None:
        counts = Counter(order.status for order in orders)
        rows = [(status, counts[status]) for status in ORDER_STATUSES if counts[status]]
        self._status_table.setRowCount(len(rows))
        for row, (status, count) in enumerate(rows):
            self._status_table.setItem(row, 0, QTableWidgetItem(status))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._status_table.setItem(row, 1, count_item)

    def _populate_recent(self, orders: list[ServiceOrder]) -> None:
        self._recent_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            order_item = QTableWidgetItem(order.order_number)
            order_item.setData(Qt.ItemDataRole.UserRole, order.id)
            self._recent_table.setItem(row, 0, order_item)
            date_text = order.intake_date.strftime("%Y-%m-%d") if order.intake_date else ""
            self._recent_table.setItem(row, 1, QTableWidgetItem(date_text))
            customer = order.customer.full_name if order.customer else ""
            self._recent_table.setItem(row, 2, QTableWidgetItem(customer))
            equipment = order.equipment
            equipment_text = ""
            if equipment:
                equipment_text = " ".join(
                    part
                    for part in (equipment.equipment_type, equipment.brand or "", equipment.model or "")
                    if part
                )
            self._recent_table.setItem(row, 3, QTableWidgetItem(equipment_text))
            self._recent_table.setItem(row, 4, QTableWidgetItem(order.status))
            self._recent_table.setItem(row, 5, QTableWidgetItem(format_money(order.balance)))

    def _open_recent_order(self, row: int, _column: int) -> None:
        item = self._recent_table.item(row, 0)
        if item:
            order_id = item.data(Qt.ItemDataRole.UserRole)
            if order_id is not None:
                self.order_opened.emit(order_id)
