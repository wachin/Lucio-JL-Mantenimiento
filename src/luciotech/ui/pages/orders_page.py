"""Página de lista de órdenes de servicio."""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QHeaderView,
    QCheckBox,
    QGroupBox,
    QDateEdit,
    QMessageBox,
    QMenu,
)
from PyQt6.QtGui import QKeySequence

from luciotech.config import ORDER_STATUSES, PRIORITIES
from luciotech.database.models import ServiceOrder
from luciotech.services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrdersPage(QWidget):
    """Página con lista avanzada de órdenes."""

    order_opened = pyqtSignal(int)  # order_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_service = OrderService()
        self._orders: list[ServiceOrder] = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_filters)
        self._init_ui()
        self._load_orders()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Texto libre: orden, cliente, equipo, serie...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)

        self._btn_new = QPushButton("Nueva recepción")
        self._btn_new.setShortcut("Ctrl+N")
        self._btn_new.clicked.connect(lambda: self.order_opened.emit(-1))  # -1 = nueva
        search_layout.addWidget(self._btn_new)

        self._btn_refresh = QPushButton("Actualizar")
        self._btn_refresh.clicked.connect(self._load_orders)
        search_layout.addWidget(self._btn_refresh)

        layout.addLayout(search_layout)

        # Filtros avanzados
        filter_group = QGroupBox("Filtros avanzados")
        filter_layout = QHBoxLayout(filter_group)

        self._filter_status = QComboBox()
        self._filter_status.addItem("Todos los estados")
        for s in ORDER_STATUSES:
            self._filter_status.addItem(s)
        self._filter_status.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self._filter_status)

        self._filter_priority = QComboBox()
        self._filter_priority.addItem("Todas")
        for p in PRIORITIES:
            self._filter_priority.addItem(p)
        self._filter_priority.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Prioridad:"))
        filter_layout.addWidget(self._filter_priority)

        self._chk_balance = QCheckBox("Con saldo pendiente")
        self._chk_balance.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self._chk_balance)

        self._chk_overdue = QCheckBox("Retrasadas")
        self._chk_overdue.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self._chk_overdue)

        filter_layout.addWidget(QLabel("Desde:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Hasta:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_to)

        self._btn_clear_filters = QPushButton("Limpiar filtros")
        self._btn_clear_filters.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self._btn_clear_filters)

        layout.addWidget(filter_group)

        # Tabla de órdenes
        self._table = QTableWidget()
        self._table.setColumnCount(13)
        self._table.setHorizontalHeaderLabels([
            "Nº Orden",
            "Fecha ingreso",
            "Cliente",
            "Teléfono",
            "Tipo equipo",
            "Marca",
            "Modelo",
            "Nº Serie",
            "Problema",
            "Estado",
            "Prioridad",
            "Total",
            "Saldo",
        ])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        # Configurar headers
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

        # Contador
        self._count_label = QLabel("0 órdenes")
        self._count_label.setStyleSheet("padding: 8px; font-size: 13px;")
        layout.addWidget(self._count_label)

    def _on_search_changed(self, text: str) -> None:
        self._search_timer.start(400)  # Debounce 400ms

    def _on_filter_changed(self) -> None:
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self._search_input.text().strip()
        status = self._filter_status.currentText()
        priority = self._filter_priority.currentText()
        has_balance = self._chk_balance.isChecked()
        is_overdue = self._chk_overdue.isChecked()

        date_from = None
        if self._date_from.date().isValid() and self._date_from.date().year() > 2000:
            date_from = datetime(
                self._date_from.date().year(),
                self._date_from.date().month(),
                self._date_from.date().day(),
            )

        date_to = None
        if self._date_to.date().isValid() and self._date_to.date().year() > 2000:
            date_to = datetime(
                self._date_to.date().year(),
                self._date_to.date().month(),
                self._date_to.date().day(),
                23, 59, 59,
            )

        status_filter = status if status != "Todos los estados" else ""
        priority_filter = priority if priority != "Todas" else ""

        self._orders = self._order_service.search(
            query_text=query,
            status=status_filter,
            priority=priority_filter,
            has_balance=has_balance,
            is_overdue=is_overdue,
            date_from=date_from,
            date_to=date_to,
        )
        self._populate_table()

    def _clear_filters(self) -> None:
        self._search_input.clear()
        self._filter_status.setCurrentIndex(0)
        self._filter_priority.setCurrentIndex(0)
        self._chk_balance.setChecked(False)
        self._chk_overdue.setChecked(False)
        self._load_orders()

    def _load_orders(self) -> None:
        self._orders = self._order_service.get_all()
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(0)
        for row, order in enumerate(self._orders):
            self._table.insertRow(row)
            customer = order.customer
            equipment = order.equipment

            self._table.setItem(row, 0, QTableWidgetItem(order.order_number))
            self._table.setItem(row, 1, QTableWidgetItem(order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else ""))
            self._table.setItem(row, 2, QTableWidgetItem(customer.full_name if customer else ""))
            self._table.setItem(row, 3, QTableWidgetItem(customer.phone_primary if customer else ""))
            self._table.setItem(row, 4, QTableWidgetItem(equipment.equipment_type if equipment else ""))
            self._table.setItem(row, 5, QTableWidgetItem(equipment.brand or "" if equipment else ""))
            self._table.setItem(row, 6, QTableWidgetItem(equipment.model or "" if equipment else ""))
            self._table.setItem(row, 7, QTableWidgetItem(equipment.serial_number or "" if equipment else ""))
            self._table.setItem(row, 8, QTableWidgetItem((order.reported_problem or "")[:80]))
            self._table.setItem(row, 9, QTableWidgetItem(order.status))
            self._table.setItem(row, 10, QTableWidgetItem(order.priority))
            self._table.setItem(row, 11, QTableWidgetItem(f"${order.total:,.2f}"))
            self._table.setItem(row, 12, QTableWidgetItem(f"${order.balance:,.2f}"))

            # Color por estado
            status_color = self._get_status_color(order.status)
            if status_color:
                for col in range(13):
                    item = self._table.item(row, col)
                    if item:
                        item.setBackground(status_color)

        self._count_label.setText(f"{len(self._orders)} órdenes")

    def _get_status_color(self, status: str) -> Qt.GlobalColor | None:
        """Color visual para cada estado."""
        colors = {
            "Recibido": Qt.GlobalColor.cyan,
            "Pendiente de diagnóstico": Qt.GlobalColor.yellow,
            "Diagnosticado": Qt.GlobalColor.lightGray,
            "Esperando aprobación": Qt.GlobalColor.magenta,
            "Esperando repuesto": Qt.GlobalColor.darkYellow,
            "En reparación": Qt.GlobalColor.blue,
            "Reparado": Qt.GlobalColor.darkGreen,
            "Listo para entregar": Qt.GlobalColor.green,
            "Entregado": Qt.GlobalColor.gray,
            "No reparable": Qt.GlobalColor.red,
            "Cancelado": Qt.GlobalColor.darkGray,
        }
        return colors.get(status)

    def _on_double_click(self) -> None:
        row = self._table.currentRow()
        if row >= 0 and row < len(self._orders):
            order = self._orders[row]
            self.order_opened.emit(order.id)

    def _on_context_menu(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._orders):
            return
        order = self._orders[row]

        menu = QMenu(self)
        open_action = menu.addAction("Abrir orden")
        open_action.triggered.connect(lambda: self.order_opened.emit(order.id))

        menu.addSeparator()
        delete_action = menu.addAction("Eliminar (papelera)")
        delete_action.triggered.connect(lambda: self._soft_delete(order))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _soft_delete(self, order: ServiceOrder) -> None:
        """Eliminar lógicamente una orden."""
        reply = QMessageBox.question(
            self,
            "Eliminar orden",
            f"¿Mover la orden {order.order_number} a la papelera?\nNo se eliminará permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._order_service.order_repo.soft_delete(order)
            self._load_orders()
            logger.info("Orden eliminada (papelera): %s", order.order_number)
