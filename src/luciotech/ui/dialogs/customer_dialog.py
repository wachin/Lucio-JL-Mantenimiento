"""Diálogo para crear o seleccionar un cliente."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QWidget,
)

from luciotech.database.models import Customer
from luciotech.services.order_service import CustomerService

logger = logging.getLogger(__name__)


class CustomerSelectDialog(QDialog):
    """Diálogo para buscar/seleccionar o crear un cliente."""

    customer_selected = pyqtSignal(object)  # Customer instance

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = CustomerService()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._search)
        self._selected_customer: Customer | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Seleccionar o crear cliente")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar cliente:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Nombre, cédula, teléfono...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)

        self._btn_create = QPushButton("Crear nuevo")
        self._btn_create.clicked.connect(self._create_new)
        search_layout.addWidget(self._btn_create)

        self._btn_select = QPushButton("Seleccionar")
        self._btn_select.clicked.connect(self._confirm_selection)
        self._btn_select.setEnabled(False)
        search_layout.addWidget(self._btn_select)
        layout.addLayout(search_layout)

        # Splitter: lista + formulario
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Lista de resultados
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_list_selection)
        splitter.addWidget(self._list)

        # Formulario de edición
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        self._name_input = QLineEdit()
        self._id_input = QLineEdit()
        self._phone_input = QLineEdit()
        self._phone2_input = QLineEdit()
        self._email_input = QLineEdit()
        self._address_input = QLineEdit()
        self._notes_input = QLineEdit()

        form_layout.addRow("Nombre completo *:", self._name_input)
        form_layout.addRow("Cédula/RUC/ID:", self._id_input)
        form_layout.addRow("Teléfono principal *:", self._phone_input)
        form_layout.addRow("Teléfono secundario:", self._phone2_input)
        form_layout.addRow("Correo electrónico:", self._email_input)
        form_layout.addRow("Dirección:", self._address_input)
        form_layout.addRow("Notas:", self._notes_input)

        splitter.addWidget(form_widget)
        splitter.setSizes([300, 400])
        layout.addWidget(splitter)

        # Botones
        button_layout = QHBoxLayout()
        self._btn_save = QPushButton("Guardar cambios")
        self._btn_save.clicked.connect(self._save_customer)
        self._btn_save.setEnabled(False)
        button_layout.addWidget(self._btn_save)

        self._btn_new_from_form = QPushButton("Guardar como nuevo")
        self._btn_new_from_form.clicked.connect(self._save_as_new)
        button_layout.addWidget(self._btn_new_from_form)

        self._btn_cancel = QPushButton("Cancelar")
        self._btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self._btn_cancel)
        layout.addLayout(button_layout)

    def _on_search_changed(self, text: str) -> None:
        self._search_timer.start(300)

    def _search(self) -> None:
        query = self._search_input.text().strip()
        self._list.clear()
        if not query:
            return
        customers = self._service.search(query)
        for c in customers:
            item = QListWidgetItem(f"{c.full_name} — {c.id_number or 'Sin ID'} — {c.phone_primary}")
            item.setData(Qt.ItemDataRole.UserRole, c)
            self._list.addItem(item)

    def _on_list_selection(self, row: int) -> None:
        if row < 0:
            self._btn_select.setEnabled(False)
            self._btn_save.setEnabled(False)
            self._clear_form()
            return
        item = self._list.item(row)
        customer: Customer = item.data(Qt.ItemDataRole.UserRole)
        self._populate_form(customer)
        self._btn_select.setEnabled(True)
        self._btn_save.setEnabled(True)

    def _populate_form(self, customer: Customer) -> None:
        self._name_input.setText(customer.full_name)
        self._id_input.setText(customer.id_number or "")
        self._phone_input.setText(customer.phone_primary)
        self._phone2_input.setText(customer.phone_secondary or "")
        self._email_input.setText(customer.email or "")
        self._address_input.setText(customer.address or "")
        self._notes_input.setText(customer.notes or "")

    def _clear_form(self) -> None:
        self._name_input.clear()
        self._id_input.clear()
        self._phone_input.clear()
        self._phone2_input.clear()
        self._email_input.clear()
        self._address_input.clear()
        self._notes_input.clear()

    def _get_form_data(self) -> dict:
        return {
            "full_name": self._name_input.text().strip(),
            "id_number": self._id_input.text().strip(),
            "phone_primary": self._phone_input.text().strip(),
            "phone_secondary": self._phone2_input.text().strip(),
            "email": self._email_input.text().strip(),
            "address": self._address_input.text().strip(),
            "notes": self._notes_input.text().strip(),
        }

    def _confirm_selection(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        item = self._list.item(row)
        customer: Customer = item.data(Qt.ItemDataRole.UserRole)
        self._selected_customer = customer
        self.customer_selected.emit(customer)
        self.accept()

    def _create_new(self) -> None:
        """Limpiar formulario para crear un nuevo cliente."""
        self._list.clear()
        self._clear_form()
        self._btn_select.setEnabled(False)
        self._name_input.setFocus()

    def start_new_customer(self) -> None:
        """Preparar el diálogo para registrar un cliente nuevo."""
        self.setWindowTitle("Nuevo cliente")
        self._create_new()
        self._btn_select.hide()
        self._btn_save.hide()
        self._btn_new_from_form.setText("Guardar cliente")

    def edit_customer(self, customer: Customer) -> None:
        """Preparar el diálogo para editar un cliente concreto."""
        self.setWindowTitle(f"Editar cliente — {customer.full_name}")
        self._list.clear()
        item = QListWidgetItem(
            f"{customer.full_name} — {customer.id_number or 'Sin ID'} — "
            f"{customer.phone_primary}"
        )
        item.setData(Qt.ItemDataRole.UserRole, customer)
        self._list.addItem(item)
        self._list.setCurrentItem(item)
        self._btn_select.hide()
        self._btn_new_from_form.hide()

    def _save_customer(self) -> None:
        """Actualizar cliente existente."""
        row = self._list.currentRow()
        if row < 0:
            return
        item = self._list.item(row)
        customer: Customer = item.data(Qt.ItemDataRole.UserRole)

        try:
            data = self._get_form_data()
            customer = self._service.update_customer(customer, **data)
            self._selected_customer = customer
            QMessageBox.information(self, "Actualizado", f"Cliente {customer.full_name} actualizado.")
            self.customer_selected.emit(customer)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _save_as_new(self) -> None:
        """Crear nuevo cliente desde el formulario."""
        try:
            data = self._get_form_data()
            customer = self._service.create_customer(**data)
            self._selected_customer = customer
            QMessageBox.information(self, "Creado", f"Cliente {customer.full_name} creado exitosamente.")
            self.customer_selected.emit(customer)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def get_selected_customer(self) -> Customer | None:
        return self._selected_customer
