"""Formulario de nueva recepción de equipo."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

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
    QFileDialog,
)

from luciotech.config import PRIORITIES, ORDER_STATUSES, ACCESSORIES_BY_TYPE
from luciotech.database.models import Customer, Equipment
from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
from luciotech.services.settings_service import SettingsService
from luciotech.ui.dialogs.customer_dialog import CustomerSelectDialog

VALID_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

logger = logging.getLogger(__name__)


class ReceptionPage(QWidget):
    """Formulario de nueva recepción organizado por secciones."""

    order_created = pyqtSignal(int)  # order_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._customer_service = CustomerService()
        self._equipment_service = EquipmentService()
        self._order_service = OrderService()
        self._settings_service = SettingsService()
        self._selected_customer: Customer | None = None
        self._accessory_checks: list[QCheckBox] = []
        self._pending_photos: list[str] = []
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

        # Sección: Fotografías
        photos_group = self._create_photos_section()
        form_layout.addWidget(photos_group)

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
        self._equip_type.addItems(self._settings_service.get_equipment_types())
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

        self._on_type_changed(self._equip_type.currentText())

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
        self._recv_technician.setText(
            self._settings_service.get("technician_name", "Ing. Joseph Lucio")
        )
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

    def _create_photos_section(self) -> QGroupBox:
        group = QGroupBox("Fotografías del equipo (opcional)")
        layout = QVBoxLayout(group)

        btn_layout = QHBoxLayout()
        self._btn_add_photos = QPushButton("📷 Seleccionar archivos")
        self._btn_add_photos.clicked.connect(self._import_photos)
        btn_layout.addWidget(self._btn_add_photos)

        self._btn_add_folder = QPushButton("📁 Desde carpeta")
        self._btn_add_folder.clicked.connect(self._import_photos_from_folder)
        btn_layout.addWidget(self._btn_add_folder)

        self._btn_clear_photos = QPushButton("🗑 Limpiar")
        self._btn_clear_photos.clicked.connect(self._clear_photos)
        btn_layout.addWidget(self._btn_clear_photos)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._photos_label = QLabel("Ninguna foto seleccionada")
        self._photos_label.setStyleSheet("color: palette(mid); padding: 4px;")
        layout.addWidget(self._photos_label)

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
        dialog.start_new_customer()
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

    def _import_photos(self) -> None:
        """Seleccionar archivos de imagen para importar tras crear la orden."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar fotografías", "",
            "Imágenes (*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tiff);;Todos los archivos (*)",
        )
        if not files:
            return
        valid = [f for f in files if Path(f).suffix.lower() in VALID_PHOTO_EXTENSIONS]
        self._pending_photos.extend(valid)
        self._update_photos_label()

    def _import_photos_from_folder(self) -> None:
        """Importar todas las imágenes de una carpeta."""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de fotografías")
        if not folder:
            return
        from pathlib import Path as _Path
        valid = [
            str(p) for p in _Path(folder).iterdir()
            if p.is_file() and p.suffix.lower() in VALID_PHOTO_EXTENSIONS
        ]
        self._pending_photos.extend(valid)
        self._update_photos_label()

    def _clear_photos(self) -> None:
        self._pending_photos.clear()
        self._update_photos_label()

    def _update_photos_label(self) -> None:
        count = len(self._pending_photos)
        if count == 0:
            self._photos_label.setText("Ninguna foto seleccionada")
        else:
            self._photos_label.setText(f"{count} fotografía(s) seleccionada(s)")

    def _import_pending_photos(self, order_id: int, order_number: str) -> None:
        """Importar las fotos pendientes tras crear la orden."""
        if not self._pending_photos:
            return
        try:
            from luciotech.services.image_service import PhotoService
            photo_svc = PhotoService()
            photo_svc.add_photos(order_id, order_number, self._pending_photos, "Estado al recibir")
            logger.info("%d fotos importadas para orden %s", len(self._pending_photos), order_number)
        except Exception:
            logger.exception("Error importando fotos de la recepción")

    def _validate_form(self) -> str | None:
        """Validar el formulario. Retorna mensaje de error o None si es válido."""
        if not self._selected_customer:
            return "Debe seleccionar o crear un cliente."

        problem = self._equip_problem.toPlainText().strip()
        if not problem:
            return "Debe describir el problema reportado."

        if not self._equip_type.currentText().strip():
            return "Debe seleccionar un tipo de equipo."

        # Validar fecha estimada
        if self._recv_estimated.date().isValid() and self._recv_estimated.date().year() > 2000:
            estimated = self._recv_estimated.date()
            intake = self._recv_date.date()
            if estimated < intake:
                return "La fecha estimada de entrega no puede ser anterior a la fecha de ingreso."

        # Validar anticipo
        diag_cost = self._recv_diag_cost.value()
        advance = self._recv_advance.value()
        if advance > 0 and diag_cost > 0 and advance > diag_cost:
            return "El anticipo no puede superar el costo de diagnóstico."

        return None

    def _show_confirmation(self, order_number: str, customer_name: str, equipment_info: str, total: float) -> bool:
        """Mostrar pantalla de confirmación antes de guardar."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar recepción")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Revise los datos antes de guardar:")
        msg.setDetailedText(
            f"Número de orden: {order_number}\n"
            f"Cliente: {customer_name}\n"
            f"Equipo: {equipment_info}\n"
            f"Costo diagnóstico: ${self._recv_diag_cost.value():,.2f}\n"
            f"Anticipo: ${self._recv_advance.value():,.2f}\n"
            f"Saldo: ${total:,.2f}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg.button(QMessageBox.StandardButton.Yes).setText("Confirmar")
        msg.button(QMessageBox.StandardButton.No).setText("Cancelar")
        return msg.exec() == QMessageBox.StandardButton.Yes

    def _save_reception(self) -> None:
        """Guardar la recepción completa."""
        error = self._validate_form()
        if error:
            QMessageBox.warning(self, "Error", error)
            return

        try:
            # Generar número de orden para la confirmación
            order_number = self._order_service.generate_order_number()
            customer = self._selected_customer
            equipment_info = (
                f"{self._equip_type.currentText()} "
                f"{self._equip_brand.text()} {self._equip_model.text()}".strip()
            )
            diag_cost = self._recv_diag_cost.value()
            advance = self._recv_advance.value()
            balance = diag_cost - advance

            if not self._show_confirmation(order_number, customer.full_name, equipment_info, balance):
                return

            # Actualizar cliente con datos del formulario
            customer = self._customer_service.update_customer(
                customer,
                full_name=customer.full_name,
                id_number=self._cust_id.text().strip(),
                phone_primary=self._cust_phone.text().strip(),
                phone_secondary=self._cust_phone2.text().strip(),
                email=self._cust_email.text().strip(),
                address=self._cust_address.text().strip(),
                notes=self._cust_notes.text().strip(),
            )

            # Crear equipo
            problem = self._equip_problem.toPlainText().strip()
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
                diagnostic_cost=diag_cost,
                advance_payment=advance,
                status=self._recv_status.currentText(),
                reported_problem=problem,
            )

            # Importar fotos pendientes
            self._import_pending_photos(order.id, order.order_number)

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
        self._recv_technician.setText(
            self._settings_service.get("technician_name", "Ing. Joseph Lucio")
        )
        for cb in self._accessory_checks:
            cb.setChecked(False)
        self._pending_photos.clear()
        self._update_photos_label()

    def refresh_settings(self) -> None:
        """Aplicar catálogos y valores predeterminados recién guardados."""
        current_type = self._equip_type.currentText()
        self._settings_service.session.expire_all()
        self._equip_type.blockSignals(True)
        self._equip_type.clear()
        self._equip_type.addItems(self._settings_service.get_equipment_types())
        index = self._equip_type.findText(current_type)
        if index >= 0:
            self._equip_type.setCurrentIndex(index)
        self._equip_type.blockSignals(False)
        self._on_type_changed(self._equip_type.currentText())
        if not self._recv_technician.text().strip():
            self._recv_technician.setText(
                self._settings_service.get("technician_name", "Ing. Joseph Lucio")
            )
