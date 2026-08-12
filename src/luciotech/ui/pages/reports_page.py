"""Página de reportes con filtros y exportación."""

from __future__ import annotations

import csv
import logging
from datetime import datetime, date
from pathlib import Path
from io import StringIO

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QTabWidget,
)
from PyQt6.QtGui import QKeySequence

from luciotech.config import ORDER_STATUSES, EQUIPMENT_TYPES
from luciotech.database.models import ServiceOrder
from luciotech.database.connection import get_session
from luciotech.database.repositories import OrderRepo
from luciotech.reports.pdf_service import PDFBuilder, A4

logger = logging.getLogger(__name__)


class ReportsPage(QWidget):
    """Página de reportes con múltiples tipos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = get_session()
        self._order_repo = OrderRepo(self._session)
        self._current_data: list[list[str]] = []
        self._current_headers: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Filtros
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("Desde:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setDate(date.today().replace(day=1))
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Hasta:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setDate(date.today())
        filter_layout.addWidget(self._date_to)

        filter_layout.addWidget(QLabel("Estado:"))
        self._filter_status = QComboBox()
        self._filter_status.addItem("Todos")
        self._filter_status.addItems(ORDER_STATUSES)
        filter_layout.addWidget(self._filter_status)

        self._btn_run = QPushButton("Generar reporte")
        self._btn_run.clicked.connect(self._generate_report)
        filter_layout.addWidget(self._btn_run)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Tabs de tipos de reporte
        self._tabs = QTabWidget()

        # Tab: Tabla de resultados
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self._table)

        # Botones de exportación
        export_layout = QHBoxLayout()
        self._btn_export_pdf = QPushButton("📄 Exportar PDF")
        self._btn_export_pdf.clicked.connect(self._export_pdf)
        export_layout.addWidget(self._btn_export_pdf)

        self._btn_export_csv = QPushButton("📊 Exportar CSV")
        self._btn_export_csv.clicked.connect(self._export_csv)
        export_layout.addWidget(self._btn_export_csv)

        self._lbl_count = QLabel("0 registros")
        export_layout.addWidget(self._lbl_count)
        export_layout.addStretch()
        table_layout.addLayout(export_layout)

        self._tabs.addTab(table_tab, "Resultados")

        # Tab: Resumen económico
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        self._summary_table = QTableWidget()
        self._summary_table.setColumnCount(2)
        self._summary_table.setHorizontalHeaderLabels(["Concepto", "Valor"])
        self._summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        summary_layout.addWidget(self._summary_table)
        self._tabs.addTab(summary_tab, "Resumen económico")

        layout.addWidget(self._tabs)

    def _generate_report(self) -> None:
        """Generar reporte con filtros."""
        date_from = datetime(
            self._date_from.date().year(),
            self._date_from.date().month(),
            self._date_from.date().day(),
        )
        date_to = datetime(
            self._date_to.date().year(),
            self._date_to.date().month(),
            self._date_to.date().day(),
            23, 59, 59,
        )
        status = self._filter_status.currentText()
        status_filter = status if status != "Todos" else ""

        orders = self._order_repo.search(
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
        )

        self._current_headers = [
            "Nº Orden", "Fecha", "Cliente", "Teléfono", "Equipo",
            "Marca", "Estado", "Prioridad", "Total", "Saldo",
        ]
        self._current_data = []
        total_income = 0.0
        total_balance = 0.0
        count_by_status: dict[str, int] = {}

        for order in orders:
            customer = order.customer
            equipment = order.equipment
            row = [
                order.order_number,
                order.intake_date.strftime("%Y-%m-%d") if order.intake_date else "",
                customer.full_name if customer else "",
                customer.phone_primary if customer else "",
                equipment.equipment_type if equipment else "",
                f"{equipment.brand or ''} {equipment.model or ''}".strip() if equipment else "",
                order.status,
                order.priority,
                f"${order.total:,.2f}",
                f"${order.balance:,.2f}",
            ]
            self._current_data.append(row)
            total_income += order.total
            total_balance += order.balance
            count_by_status[order.status] = count_by_status.get(order.status, 0) + 1

        # Tabla de resultados
        self._table.setColumnCount(len(self._current_headers))
        self._table.setHorizontalHeaderLabels(self._current_headers)
        self._table.setRowCount(0)
        for r, row_data in enumerate(self._current_data):
            self._table.insertRow(r)
            for c, val in enumerate(row_data):
                self._table.setItem(r, c, QTableWidgetItem(val))

        self._lbl_count.setText(f"{len(self._current_data)} registros")

        # Resumen económico
        self._summary_table.setRowCount(0)
        summary_items = [
            ("Total de órdenes", str(len(orders))),
            ("Ingresos totales", f"${total_income:,.2f}"),
            ("Saldo pendiente", f"${total_balance:,.2f}"),
            ("Rango de fechas", f"{date_from.strftime('%Y-%m-%d')} a {date_to.strftime('%Y-%m-%d')}"),
        ]
        for status_name, count in sorted(count_by_status.items()):
            summary_items.append((f"Órdenes: {status_name}", str(count)))

        for r, (concept, value) in enumerate(summary_items):
            self._summary_table.insertRow(r)
            self._summary_table.setItem(r, 0, QTableWidgetItem(concept))
            self._summary_table.setItem(r, 1, QTableWidgetItem(value))

    def _export_pdf(self) -> None:
        if not self._current_data:
            QMessageBox.warning(self, "Sin datos", "Genere un reporte primero.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        builder = PDFBuilder(title="Reporte de órdenes")
        builder.story.append(builder._build_table(self._current_headers, self._current_data))
        builder.save_to_file(path)
        QMessageBox.information(self, "PDF exportado", f"Reporte guardado en:\n{path}")
        logger.info("Reporte PDF exportado: %s", path)

    def _export_csv(self) -> None:
        if not self._current_data:
            QMessageBox.warning(self, "Sin datos", "Genere un reporte primero.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._current_headers)
            writer.writerows(self._current_data)

        QMessageBox.information(self, "CSV exportado", f"Reporte guardado en:\n{path}")
        logger.info("Reporte CSV exportado: %s", path)
