"""Diálogo de consulta y edición de equipos."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from luciotech.database.models import Equipment
from luciotech.database.repositories import OrderRepo
from luciotech.database.connection import get_session
from luciotech.services.order_service import EquipmentService
from luciotech.services.settings_service import SettingsService


class EquipmentEditDialog(QDialog):
    """Editar la ficha de un equipo registrado."""

    def __init__(self, equipment: Equipment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = EquipmentService()
        managed_equipment = self._service.get_by_id(equipment.id)
        if managed_equipment is None:
            raise ValueError("El equipo ya no existe")
        self._equipment = managed_equipment
        self._order_repo = OrderRepo(get_session())
        self._init_ui()
        self._load_equipment()
        self._load_history()

    def _init_ui(self) -> None:
        self.setWindowTitle("Editar equipo")
        self.setMinimumSize(620, 680)
        layout = QVBoxLayout(self)

        # Tabs: Datos / Historial
        tabs = QTabWidget()

        # --- Pestaña: Datos del equipo ---
        form_tab = QWidget()
        form_layout = QFormLayout(form_tab)

        self._type = QComboBox()
        self._type.setEditable(True)
        self._type.addItems(SettingsService().get_equipment_types())
        form_layout.addRow("Tipo de equipo *:", self._type)

        self._brand = QLineEdit()
        self._model = QLineEdit()
        self._serial = QLineEdit()
        self._color = QLineEdit()
        self._os = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_password = QCheckBox("Mostrar contraseña/PIN")
        self._show_password.toggled.connect(self._toggle_password)
        self._accessories = QLineEdit()
        self._physical_state = QTextEdit()
        self._reported_problem = QTextEdit()
        self._intake_notes = QTextEdit()

        for editor in (self._physical_state, self._reported_problem, self._intake_notes):
            editor.setMaximumHeight(85)

        form_layout.addRow("Marca:", self._brand)
        form_layout.addRow("Modelo:", self._model)
        form_layout.addRow("Número de serie:", self._serial)
        form_layout.addRow("Color:", self._color)
        form_layout.addRow("Sistema operativo:", self._os)
        form_layout.addRow("Contraseña/PIN:", self._password)
        form_layout.addRow("", self._show_password)
        form_layout.addRow("Accesorios:", self._accessories)
        form_layout.addRow("Estado físico:", self._physical_state)
        form_layout.addRow("Problema reportado:", self._reported_problem)
        form_layout.addRow("Observaciones de ingreso:", self._intake_notes)
        tabs.addTab(form_tab, "Datos del equipo")

        # --- Pestaña: Historial de servicio ---
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        self._history_label = QLabel("Órdenes de servicio para este equipo:")
        history_layout.addWidget(self._history_label)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(
            ["N.º Orden", "Fecha", "Estado", "Cliente", "Problema"]
        )
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._history_table.setAlternatingRowColors(True)
        header = self._history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self._history_table)

        self._no_history_label = QLabel("Sin órdenes registradas.")
        self._no_history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_layout.addWidget(self._no_history_label)

        tabs.addTab(history_tab, "Historial")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar cambios")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_equipment(self) -> None:
        equipment = self._equipment
        index = self._type.findText(equipment.equipment_type)
        if index >= 0:
            self._type.setCurrentIndex(index)
        else:
            self._type.setCurrentText(equipment.equipment_type)
        self._brand.setText(equipment.brand or "")
        self._model.setText(equipment.model or "")
        self._serial.setText(equipment.serial_number or "")
        self._color.setText(equipment.color or "")
        self._os.setText(equipment.os or "")
        self._password.setText(equipment.password or "")
        self._accessories.setText(equipment.accessories or "")
        self._physical_state.setPlainText(equipment.physical_state or "")
        self._reported_problem.setPlainText(equipment.reported_problem or "")
        self._intake_notes.setPlainText(equipment.intake_notes or "")

    def _load_history(self) -> None:
        """Cargar el historial de órdenes de servicio del equipo."""
        orders = self._order_repo.get_by_equipment(self._equipment.id)
        self._history_table.setRowCount(len(orders))

        if not orders:
            self._history_table.hide()
            self._no_history_label.show()
            return

        self._history_table.show()
        self._no_history_label.hide()

        for row, order in enumerate(orders):
            # Número de orden
            num_item = QTableWidgetItem(order.order_number or "")
            num_item.setData(Qt.ItemDataRole.UserRole, order)
            self._history_table.setItem(row, 0, num_item)

            # Fecha de ingreso
            date_str = ""
            if order.intake_date:
                date_str = order.intake_date.strftime("%Y-%m-%d")
            self._history_table.setItem(row, 1, QTableWidgetItem(date_str))

            # Estado
            self._history_table.setItem(row, 2, QTableWidgetItem(order.status or ""))

            # Cliente
            customer_name = ""
            if order.customer:
                customer_name = order.customer.full_name or ""
            self._history_table.setItem(row, 3, QTableWidgetItem(customer_name))

            # Problema reportado
            problem = order.reported_problem or ""
            if len(problem) > 80:
                problem = problem[:77] + "..."
            self._history_table.setItem(row, 4, QTableWidgetItem(problem))

    def _toggle_password(self, visible: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self._password.setEchoMode(mode)

    def _save(self) -> None:
        try:
            self._service.update_equipment(
                self._equipment,
                equipment_type=self._type.currentText(),
                brand=self._brand.text(),
                model=self._model.text(),
                serial_number=self._serial.text(),
                color=self._color.text(),
                os=self._os.text(),
                password=self._password.text(),
                accessories=self._accessories.text(),
                physical_state=self._physical_state.toPlainText(),
                reported_problem=self._reported_problem.toPlainText(),
                intake_notes=self._intake_notes.toPlainText(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo guardar", str(error))
            return
        self.accept()
