"""Diálogo de ficha completa del cliente."""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QWidget,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QAbstractItemView,
)

from luciotech.database.models import Customer
from luciotech.database.connection import get_session
from luciotech.database.repositories import OrderRepo, PaymentRepo

logger = logging.getLogger(__name__)


class CustomerDetailDialog(QDialog):
    """Ficha completa del cliente con equipos, órdenes, pagos y saldos."""

    def __init__(self, customer: Customer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._customer = customer
        self.setWindowTitle(f"Ficha — {customer.full_name}")
        self.setMinimumSize(800, 600)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Datos básicos
        info_group = QGroupBox("Datos del cliente")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Nombre:", QLabel(self._customer.full_name))
        info_layout.addRow("Identificación:", QLabel(self._customer.id_number or "—"))
        info_layout.addRow("Teléfono:", QLabel(self._customer.phone_primary))
        if self._customer.phone_secondary:
            info_layout.addRow("Teléfono alterno:", QLabel(self._customer.phone_secondary))
        if self._customer.email:
            info_layout.addRow("Correo:", QLabel(self._customer.email))
        if self._customer.address:
            info_layout.addRow("Dirección:", QLabel(self._customer.address))
        registered = self._customer.created_at.strftime("%Y-%m-%d") if self._customer.created_at else "—"
        info_layout.addRow("Registrado:", QLabel(registered))
        layout.addWidget(info_group)

        # Pestañas
        tabs = QTabWidget()
        tabs.addTab(self._create_orders_tab(), "Órdenes")
        tabs.addTab(self._create_equipment_tab(), "Equipos")
        tabs.addTab(self._create_payments_tab(), "Pagos y saldos")
        layout.addWidget(tabs)

        # Botón cerrar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _create_orders_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        session = get_session()
        order_repo = OrderRepo(session)
        orders = order_repo.search(query_text=self._customer.full_name)
        customer_orders = [o for o in orders if o.customer_id == self._customer.id]

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Nº Orden", "Equipo", "Estado", "Prioridad", "Total", "Saldo", "Fecha ingreso",
        ])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        table.setRowCount(len(customer_orders))
        total_balance = 0.0
        for row, order in enumerate(customer_orders):
            equip_name = ""
            if order.equipment:
                equip_name = f"{order.equipment.equipment_type} {order.equipment.brand or ''} {order.equipment.model or ''}".strip()
            table.setItem(row, 0, QTableWidgetItem(order.order_number))
            table.setItem(row, 1, QTableWidgetItem(equip_name))
            table.setItem(row, 2, QTableWidgetItem(order.status))
            table.setItem(row, 3, QTableWidgetItem(order.priority))
            table.setItem(row, 4, QTableWidgetItem(f"${order.total:,.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"${order.balance:,.2f}"))
            intake = order.intake_date.strftime("%Y-%m-%d") if order.intake_date else ""
            table.setItem(row, 6, QTableWidgetItem(intake))
            total_balance += order.balance

        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        summary = QLabel(
            f"{len(customer_orders)} orden(es) — Saldo total pendiente: ${total_balance:,.2f}"
        )
        summary.setStyleSheet("font-weight: bold; padding: 6px;")
        layout.addWidget(summary)

        # Última visita
        if customer_orders:
            last_order = max(customer_orders, key=lambda o: o.intake_date or datetime.min)
            last_date = last_order.intake_date.strftime("%Y-%m-%d") if last_order.intake_date else "—"
            last_visit = QLabel(f"Última visita: {last_date} (Orden {last_order.order_number})")
            last_visit.setStyleSheet("padding: 4px; color: palette(mid);")
            layout.addWidget(last_visit)

        return widget

    def _create_equipment_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        session = get_session()
        from luciotech.database.repositories import EquipmentRepo
        equip_repo = EquipmentRepo(session)
        equipments = equip_repo.get_by_customer(self._customer.id)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Tipo", "Marca", "Modelo", "Serie", "Color", "SO"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        table.setRowCount(len(equipments))
        for row, eq in enumerate(equipments):
            table.setItem(row, 0, QTableWidgetItem(eq.equipment_type))
            table.setItem(row, 1, QTableWidgetItem(eq.brand or ""))
            table.setItem(row, 2, QTableWidgetItem(eq.model or ""))
            table.setItem(row, 3, QTableWidgetItem(eq.serial_number or ""))
            table.setItem(row, 4, QTableWidgetItem(eq.color or ""))
            table.setItem(row, 5, QTableWidgetItem(eq.os or ""))

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        count_label = QLabel(f"{len(equipments)} equipo(s) registrado(s)")
        count_label.setStyleSheet("padding: 6px; color: palette(mid);")
        layout.addWidget(count_label)

        return widget

    def _create_payments_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        session = get_session()
        order_repo = OrderRepo(session)
        pay_repo = PaymentRepo(session)

        orders = order_repo.search(query_text=self._customer.full_name)
        customer_orders = [o for o in orders if o.customer_id == self._customer.id]

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Orden", "Fecha", "Tipo", "Método", "Monto", "Referencia"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        row = 0
        total_paid = 0.0
        total_orders = 0.0
        for order in customer_orders:
            payments = pay_repo.get_by_order(order.id)
            total_orders += order.total
            for p in payments:
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(order.order_number))
                table.setItem(row, 1, QTableWidgetItem(
                    p.payment_date.strftime("%Y-%m-%d") if p.payment_date else ""
                ))
                table.setItem(row, 2, QTableWidgetItem(p.payment_type))
                table.setItem(row, 3, QTableWidgetItem(p.payment_method))
                table.setItem(row, 4, QTableWidgetItem(f"${p.amount:,.2f}"))
                table.setItem(row, 5, QTableWidgetItem(p.reference or ""))
                total_paid += p.amount
                row += 1

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        total_balance = total_orders - total_paid
        summary = QLabel(
            f"Total órdenes: ${total_orders:,.2f} — "
            f"Pagado: ${total_paid:,.2f} — "
            f"Saldo: ${total_balance:,.2f}"
        )
        summary.setStyleSheet("font-weight: bold; padding: 6px;")
        layout.addWidget(summary)

        return widget
