"""Formulario de nueva recepción de equipo."""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QSplitter,
    QMessageBox,
    QScrollArea,
    QDoubleSpinBox,
    QTabWidget,
)

from luciotech.config import EQUIPMENT_TYPES, PRIORITIES, ORDER_STATUSES, ACCESSORIES_BY_TYPE
from luciotech.database.models import Customer, Equipment
from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
from luciotech.ui.dialogs.customer_dialog import CustomerSelectDialog

logger = logging.getLogger(__name__)


class ReceptionPage(QWidget):
    """Formulario de nueva recepción organizado por secciones."""

    order_created = pyqtSignal(int)  # order_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._customer_service = CustomerService()
        self._equipment_service = EquipmentService()
        self._order_service = OrderService()
        self._selected_customer: Customer | None = None
        self._accessory_checks: list[QCheckBox] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Scroll area para el formulario
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)

        # Sección: Cliente
        customer_group = self._create_customer_section()
        form_layout.addWidget(customer_group)

        # Sección: Equipo
        equipment_group = self._create_equipment_section()
        form_layout.addWidget(equipment_group)

        # Sección: Recepción
        reception_group = self._create_reception_section()
        form_layout.addWidget(reception_group)

        scroll.setWidget(form_container)
        layout.addWidget(scroll)

        # Botones inferiores
        button_layout = QHBoxLayout()
        self._btn_save = QPushButton("Guardar recepción")
        self._btn_save.setStyleSheet("font-size: 16px; padding: 10px 30px;")
        self._btn_save.clicked.connect(self._save_reception)
        button_layout.addWidget(self._btn_save)

        self._btn_clear = QPushButton("Limpiar formulario")
        self._btn_clear.clicked.connect(self._clear_form)
        button_layout.addWidget(self._btn_clear)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _create_customer_section(self) -> QGroupBox:
        group = QGroupBox("Datos del cliente")
        layout = QVBoxLayout(group)

        # Barra de selección
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Cliente:"))
        self._customer_display = QLineEdit()
        self._customer_display.setReadOnly(True)
        self._customer_display.setPlaceholderText("Buscar o crear cliente...")
        select_layout.addWidget(self._customer_display)

        self._btn_select_customer = QPushButton("Buscar")
        self._btn_select_customer.clicked.connect(self._open_customer_dialog)
        select_layout.addWidget(self._btn_select_customer)

        self._btn_new_customer = QPushButton("Nuevo")
        self._btn_new_customer.clicked.connect(self._open_customer_dialog_new)
        select_layout.addWidget(self._btn_new_customer)
        layout.addLayout(select_layout)

        # Campos adicionales del cliente
        form_layout = QFormLayout()
        self._cust_id = QLineEdit()
        self._cust_phone = QLineEdit()
        self._cust_phone2 = QLineEdit()
        self._cust_email = QLineEdit()
        self._cust_address = QLineEdit()
        self._cust_notes = QLineEdit()

        form_layout.addRow("Identificación:", self._cust_id)
        form_layout.addRow("Teléfono principal:", self._cust_phone)
        form_layout.addRow("Teléfono secundario:", self._cust_phone2)
        form_layout.addRow("Correo electrónico:", self._cust_email)
        form_layout.addRow("Dirección:", self._cust_address)
        form_layout.addRow("Observaciones:", self._cust_notes)
        layout.addLayout(form_layout)

        return group

    def _create_equipment_section(self) -> QGroupBox:
        group = QGroupBox("Datos del equipo")
        layout = QFormLayout(group)

        self._equip_type = QComboBox()
        self._equip_type.addItems(EQUIPMENT_TYPES)
        self._equip_type.currentTextChanged.connect(self._on_type_changed)
        layout.addRow("Tipo de equipo *:", self._equip_type)

        self._equip_brand = QLineEdit()
        layout.addRow("Marca:", self._equip_brand)

        self._equip_model = QLineEdit()
        layout.addRow("Modelo:", self._equip_model)

        self._equip_serial = QLineEdit()
        layout.addRow("Número de serie:", self._equip_serial)

        self._equip_color = QLineEdit()
        layout.addRow("Color:", self._equip_color)

        self._equip_os = QLineEdit()
        layout.addRow("Sistema operativo:", self._equip_os)

        self._equip_password = QLineEdit()
        self._equip_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Contraseña/PIN:", self._equip_password)

        self._equip_physical = QTextEdit()
        self._equip_physical.setMaximumHeight(60)
        layout.addRow("Estado físico:", self._equip_physical)

        self._equip_problem = QTextEdit()
        self._equip_problem.setMaximumHeight(80)
        layout.addRow("Problema reportado *:", self._equip_problem)

        self._equip_notes = QTextEdit()
        self._equip_notes.setMaximumHeight(60)
        layout.addRow("Observaciones de ingreso:", self._equip_notes)

        # Accesorios
        self._acc_group = QGroupBox("Accesorios recibidos")
        self._acc_layout = QVBoxLayout(self._acc_group)
        self._acc_other = QLineEdit()
        self._acc_other.setPlaceholderText("Otros accesorios (escribir)...")
        layout.addRow(self._acc_group)

        self._on_type_changed(EQUIPMENT_TYPES[0])

        return group

    def _create_reception_section(self) -> QGroupBox:
        group = QGroupBox("Recepción")
        layout = QFormLayout(group)

        # Fecha y hora
        date_layout = QHBoxLayout()
        self._recv_date = QDateEdit()
        self._recv_date.setCalendarPopup(True)
        self._recv_date.setDisplayFormat("yyyy-MM-dd")
        self._recv_date.setDate(datetime.now().date())
        date_layout.addWidget(self._recv_date)

        self._recv_time = QTimeEdit()
        self._recv_time.setDisplayFormat("HH:mm")
        self._recv_time.setTime(datetime.now().time())
        date_layout.addWidget(self._recv_time)
        layout.addRow("Fecha y hora de ingreso:", date_layout)

        # Fecha estimada
        self._recv_estimated = QDateEdit()
        self._recv_estimated.setCalendarPopup(True)
        self._recv_estimated.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("Fecha estimada de entrega:", self._recv_estimated)

        # Prioridad
        self._recv_priority = QComboBox()
        self._recv_priority.addItems(PRIORITIES)
        layout.addRow("Prioridad:", self._recv_priority)

        # Técnico
        self._recv_technician = QLineEdit()
        self._recv_technician.setPlaceholderText("Nombre del técnico")
        layout.addRow("Técnico responsable:", self._recv_technician)

        # Costos
        cost_layout = QHBoxLayout()
        self._recv_diag_cost = QDoubleSpinBox()
        self._recv_diag_cost.setMaximum(999999.99)
        self._recv_diag_cost.setPrefix("$ ")
        cost_layout.addWidget(QLabel("Costo diagnóstico:"))
        cost_layout.addWidget(self._recv_diag_cost)

        self._recv_advance = QDoubleSpinBox()
        self._recv_advance.setMaximum(999999.99)
        self._recv_advance.setPrefix("$ ")
        cost_layout.addWidget(QLabel("Anticipo:"))
        cost_layout.addWidget(self._recv_advance)
        layout.addRow(cost_layout)

        # Estado inicial
        self._recv_status = QComboBox()
        self._recv_status.addItems(ORDER_STATUSES[:3])  # Recibido, Pendiente de diagnóstico, Diagnosticado
        layout.addRow("Estado inicial:", self._recv_status)

        return group

    def _on_type_changed(self, equip_type: str) -> None:
        """Actualizar accesorios según tipo de equipo."""
        # Limpiar checkboxes anteriores
        for cb in self._accessory_checks:
            cb.deleteLater()
        self._accessory_checks.clear()

        if hasattr(self, '_acc_other') and self._acc_other:
            self._acc_other.deleteLater()

        accessories = ACCESSORIES_BY_TYPE.get(equip_type, ["Otro"])
        for acc in accessories:
            cb = QCheckBox(acc)
            self._accessory_checks.append(cb)
            if hasattr(self, '_acc_layout'):
                self._acc_layout.addWidget(cb)

        self._acc_other = QLineEdit()
        self._acc_other.setPlaceholderText("Otros accesorios (escribir)...")
        if hasattr(self, '_acc_layout'):
            self._acc_layout.addWidget(self._acc_other)

    def _open_customer_dialog(self) -> None:
        dialog = CustomerSelectDialog(self)
        if dialog.exec():
            customer = dialog.get_selected_customer()
            if customer:
                self._set_customer(customer)

    def _open_customer_dialog_new(self) -> None:
        dialog = CustomerSelectDialog(self)
        dialog._clear_form()
        dialog._list.clear()
        if dialog.exec():
            customer = dialog.get_selected_customer()
            if customer:
                self._set_customer(customer)

    def _set_customer(self, customer: Customer) -> None:
        self._selected_customer = customer
        self._customer_display.setText(f"{customer.full_name} ({customer.id_number or 'Sin ID'})")
        self._cust_id.setText(customer.id_number or "")
        self._cust_phone.setText(customer.phone_primary)
        self._cust_phone2.setText(customer.phone_secondary or "")
        self._cust_email.setText(customer.email or "")
        self._cust_address.setText(customer.address or "")
        self._cust_notes.setText(customer.notes or "")

    def _get_accessories_text(self) -> str:
        parts = []
        for cb in self._accessory_checks:
            if cb.isChecked():
                parts.append(cb.text())
        other = self._acc_other.text().strip() if hasattr(self, '_acc_other') and self._acc_other else ""
        if other:
            parts.append(other)
        return ", ".join(parts)

    def _save_reception(self) -> None:
        """Guardar la recepción completa."""
        # Validar
        if not self._selected_customer:
            QMessageBox.warning(self, "Error", "Debe seleccionar o crear un cliente.")
            return

        problem = self._equip_problem.toPlainText().strip()
        if not problem:
            QMessageBox.warning(self, "Error", "Debe describir el problema reportado.")
            return

        try:
            # Crear o actualizar cliente con datos del formulario
            customer = self._selected_customer
            if self._cust_id.text().strip():
                customer = self._customer_service.update_customer(
                    customer,
                    id_number=self._cust_id.text().strip(),
                    phone_primary=self._cust_phone.text().strip(),
                    phone_secondary=self._cust_phone2.text().strip() or None,
                    email=self._cust_email.text().strip() or None,
                    address=self._cust_address.text().strip() or None,
                    notes=self._cust_notes.text().strip() or None,
                )

            # Crear equipo
            equipment = self._equipment_service.create_equipment(
                customer_id=customer.id,
                equipment_type=self._equip_type.currentText(),
                brand=self._equip_brand.text(),
                model=self._equip_model.text(),
                serial_number=self._equip_serial.text(),
                color=self._equip_color.text(),
                os=self._equip_os.text(),
                password=self._equip_password.text(),
                accessories=self._get_accessories_text(),
                physical_state=self._equip_physical.toPlainText(),
                reported_problem=problem,
                intake_notes=self._equip_notes.toPlainText(),
            )

            # Crear orden
            intake_date = datetime(
                self._recv_date.date().year(),
                self._recv_date.date().month(),
                self._recv_date.date().day(),
                self._recv_time.time().hour(),
                self._recv_time.time().minute(),
            )

            estimated_date = None
            if self._recv_estimated.date().isValid() and self._recv_estimated.date().year() > 2000:
                estimated_date = datetime(
                    self._recv_estimated.date().year(),
                    self._recv_estimated.date().month(),
                    self._recv_estimated.date().day(),
                )

            order = self._order_service.create_order(
                customer=customer,
                equipment=equipment,
                intake_date=intake_date,
                estimated_delivery_date=estimated_date,
                priority=self._recv_priority.currentText(),
                technician=self._recv_technician.text(),
                diagnostic_cost=self._recv_diag_cost.value(),
                advance_payment=self._recv_advance.value(),
                status=self._recv_status.currentText(),
                reported_problem=problem,
            )

            QMessageBox.information(
                self,
                "Orden creada",
                f"Orden {order.order_number} creada exitosamente.",
            )
            self.order_created.emit(order.id)
            self._clear_form()

        except Exception as e:
            logger.exception("Error al crear recepción")
            QMessageBox.critical(self, "Error", f"No se pudo crear la orden: {e}")

    def _clear_form(self) -> None:
        """Limpiar todo el formulario."""
        self._selected_customer = None
        self._customer_display.clear()
        self._cust_id.clear()
        self._cust_phone.clear()
        self._cust_phone2.clear()
        self._cust_email.clear()
        self._cust_address.clear()
        self._cust_notes.clear()
        self._equip_brand.clear()
        self._equip_model.clear()
        self._equip_serial.clear()
        self._equip_color.clear()
        self._equip_os.clear()
        self._equip_password.clear()
        self._equip_physical.clear()
        self._equip_problem.clear()
        self._equip_notes.clear()
        self._recv_diag_cost.setValue(0)
        self._recv_advance.setValue(0)
        self._recv_technician.clear()
        for cb in self._accessory_checks:
            cb.setChecked(False)
