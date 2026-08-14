"""Diálogo de consulta y edición de equipos."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from luciotech.config import EQUIPMENT_TYPES
from luciotech.database.models import Equipment
from luciotech.services.order_service import EquipmentService


class EquipmentEditDialog(QDialog):
    """Editar la ficha de un equipo registrado."""

    def __init__(self, equipment: Equipment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = EquipmentService()
        managed_equipment = self._service.get_by_id(equipment.id)
        if managed_equipment is None:
            raise ValueError("El equipo ya no existe")
        self._equipment = managed_equipment
        self._init_ui()
        self._load_equipment()

    def _init_ui(self) -> None:
        self.setWindowTitle("Editar equipo")
        self.setMinimumSize(620, 680)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._type = QComboBox()
        self._type.setEditable(True)
        self._type.addItems(EQUIPMENT_TYPES)
        form.addRow("Tipo de equipo *:", self._type)

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

        form.addRow("Marca:", self._brand)
        form.addRow("Modelo:", self._model)
        form.addRow("Número de serie:", self._serial)
        form.addRow("Color:", self._color)
        form.addRow("Sistema operativo:", self._os)
        form.addRow("Contraseña/PIN:", self._password)
        form.addRow("", self._show_password)
        form.addRow("Accesorios:", self._accessories)
        form.addRow("Estado físico:", self._physical_state)
        form.addRow("Problema reportado:", self._reported_problem)
        form.addRow("Observaciones de ingreso:", self._intake_notes)
        layout.addLayout(form)

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
