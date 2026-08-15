"""Página de consulta y gestión de clientes."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from luciotech.database.models import Customer
from luciotech.services.order_service import CustomerService
from luciotech.ui.dialogs.customer_dialog import CustomerSelectDialog


class CustomersPage(QWidget):
    """Listado buscable con creación y edición de clientes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = CustomerService()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._load_customers)
        self._init_ui()
        self._load_customers()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Clientes")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 12px 0;")
        layout.addWidget(title)

        actions = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setPlaceholderText(
            "Buscar por nombre, identificación, teléfono o correo..."
        )
        self._search_input.textChanged.connect(lambda: self._search_timer.start())
        actions.addWidget(self._search_input)

        self._btn_new = QPushButton("Nuevo cliente")
        self._btn_new.clicked.connect(self._create_customer)
        actions.addWidget(self._btn_new)

        self._btn_edit = QPushButton("Editar")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_selected_customer)
        actions.addWidget(self._btn_edit)

        self._btn_detail = QPushButton("Ver ficha")
        self._btn_detail.setEnabled(False)
        self._btn_detail.clicked.connect(self._show_customer_detail)
        actions.addWidget(self._btn_detail)

        self._btn_refresh = QPushButton("Actualizar")
        self._btn_refresh.clicked.connect(self._load_customers)
        actions.addWidget(self._btn_refresh)
        layout.addLayout(actions)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Nombre",
                "Identificación",
                "Teléfono",
                "Teléfono alterno",
                "Correo",
                "Dirección",
                "Equipos",
                "Registrado",
            ]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._update_actions)
        self._table.cellDoubleClicked.connect(self._edit_selected_customer)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        self._count_label = QLabel()
        self._count_label.setStyleSheet("padding: 6px; color: palette(mid);")
        layout.addWidget(self._count_label)

    def _load_customers(self) -> None:
        # Los diálogos usan su propia sesión; descartar aquí los valores en
        # caché permite mostrar inmediatamente las altas y ediciones.
        self._service.repo.session.expire_all()
        query = self._search_input.text().strip()
        customers = self._service.search(query) if query else self._service.get_all()

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(customers))
        for row, customer in enumerate(customers):
            name_item = QTableWidgetItem(customer.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, customer)
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, QTableWidgetItem(customer.id_number or ""))
            self._table.setItem(row, 2, QTableWidgetItem(customer.phone_primary))
            self._table.setItem(row, 3, QTableWidgetItem(customer.phone_secondary or ""))
            self._table.setItem(row, 4, QTableWidgetItem(customer.email or ""))
            self._table.setItem(row, 5, QTableWidgetItem(customer.address or ""))
            self._table.setItem(row, 6, QTableWidgetItem(str(len(customer.equipments))))
            created = customer.created_at.strftime("%Y-%m-%d") if customer.created_at else ""
            self._table.setItem(row, 7, QTableWidgetItem(created))

        self._table.setSortingEnabled(True)
        self._count_label.setText(f"{len(customers)} cliente(s)")
        self._update_actions()

    def _selected_customer(self) -> Customer | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_actions(self) -> None:
        has_selection = self._selected_customer() is not None
        self._btn_edit.setEnabled(has_selection)
        self._btn_detail.setEnabled(has_selection)

    def _show_customer_detail(self) -> None:
        customer = self._selected_customer()
        if customer is None:
            return
        from luciotech.ui.dialogs.customer_detail_dialog import CustomerDetailDialog
        dialog = CustomerDetailDialog(customer, self)
        dialog.exec()

    def _create_customer(self) -> None:
        dialog = CustomerSelectDialog(self)
        dialog.start_new_customer()
        if dialog.exec():
            self._load_customers()

    def _edit_selected_customer(self, *_args) -> None:
        customer = self._selected_customer()
        if customer is None:
            return
        dialog = CustomerSelectDialog(self)
        dialog.edit_customer(customer)
        if dialog.exec():
            self._load_customers()
