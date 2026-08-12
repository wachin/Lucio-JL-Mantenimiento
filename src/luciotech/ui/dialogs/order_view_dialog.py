"""Diálogo de vista de una orden."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QComboBox,
)

from luciotech.database.models import ServiceOrder
from luciotech.services.order_service import OrderService
from luciotech.config import ORDER_STATUSES
from luciotech.ui.widgets.rich_text_edit import RichTextEdit
from luciotech.ui.widgets.photo_tab import PhotoTab
from luciotech.ui.widgets.history_timeline import HistoryTimeline

logger = logging.getLogger(__name__)


class OrderViewDialog(QDialog):
    """Diálogo para ver y editar una orden."""

    def __init__(self, order_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_id = order_id
        self._order_service = OrderService()
        self._order: ServiceOrder | None = None
        self._init_ui()
        self._load_order()

    def _init_ui(self) -> None:
        self.setWindowTitle("Orden de servicio")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # Tabs
        self._tabs = QTabWidget()

        # Tab: Resumen
        self._summary_tab = self._create_summary_tab()
        self._tabs.addTab(self._summary_tab, "Resumen")

        # Tab: Cliente
        self._customer_tab = self._create_customer_tab()
        self._tabs.addTab(self._customer_tab, "Cliente")

        # Tab: Equipo
        self._equipment_tab = self._create_equipment_tab()
        self._tabs.addTab(self._equipment_tab, "Equipo")

        # Tab: Diagnóstico (placeholder para Fase 2)
        self._diagnosis_tab = self._create_diagnosis_tab()
        self._tabs.addTab(self._diagnosis_tab, "Diagnóstico")

        # Tab: Historial
        self._history_tab = self._create_history_tab()
        self._tabs.addTab(self._history_tab, "Historial")

        # Tab: Fotografías
        self._photo_tab = QWidget()  # placeholder, created after order loaded
        self._tabs.addTab(self._photo_tab, "Fotografías")

        layout.addWidget(self._tabs)

        # Botones
        button_layout = QHBoxLayout()
        self._btn_change_status = QPushButton("Cambiar estado")
        self._btn_change_status.clicked.connect(self._change_status)
        button_layout.addWidget(self._btn_change_status)

        button_layout.addStretch()

        self._btn_close = QPushButton("Cerrar")
        self._btn_close.clicked.connect(self.accept)
        button_layout.addWidget(self._btn_close)

        layout.addLayout(button_layout)

    def _create_summary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._lbl_order_number = QLabel()
        self._lbl_order_number.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addRow("Nº Orden:", self._lbl_order_number)

        self._lbl_status = QLabel()
        layout.addRow("Estado:", self._lbl_status)

        self._lbl_priority = QLabel()
        layout.addRow("Prioridad:", self._lbl_priority)

        self._lbl_customer = QLabel()
        layout.addRow("Cliente:", self._lbl_customer)

        self._lbl_phone = QLabel()
        layout.addRow("Teléfono:", self._lbl_phone)

        self._lbl_equipment_type = QLabel()
        layout.addRow("Tipo de equipo:", self._lbl_equipment_type)

        self._lbl_brand = QLabel()
        layout.addRow("Marca:", self._lbl_brand)

        self._lbl_model = QLabel()
        layout.addRow("Modelo:", self._lbl_model)

        self._lbl_serial = QLabel()
        layout.addRow("Nº Serie:", self._lbl_serial)

        self._lbl_intake_date = QLabel()
        layout.addRow("Fecha de ingreso:", self._lbl_intake_date)

        self._lbl_estimated = QLabel()
        layout.addRow("Fecha estimada:", self._lbl_estimated)

        self._lbl_balance = QLabel()
        self._lbl_balance.setStyleSheet("font-size: 16px; color: red;")
        layout.addRow("Saldo pendiente:", self._lbl_balance)

        self._lbl_technician = QLabel()
        layout.addRow("Técnico:", self._lbl_technician)

        self._problem_display = QTextEdit()
        self._problem_display.setReadOnly(True)
        self._problem_display.setMaximumHeight(80)
        layout.addRow("Problema reportado:", self._problem_display)

        return tab

    def _create_customer_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._cust_name = QLabel()
        layout.addRow("Nombre:", self._cust_name)

        self._cust_id = QLabel()
        layout.addRow("Identificación:", self._cust_id)

        self._cust_phone = QLabel()
        layout.addRow("Teléfono:", self._cust_phone)

        self._cust_email = QLabel()
        layout.addRow("Correo:", self._cust_email)

        self._cust_address = QLabel()
        layout.addRow("Dirección:", self._cust_address)

        return tab

    def _create_equipment_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._equip_type = QLabel()
        layout.addRow("Tipo:", self._equip_type)

        self._equip_brand = QLabel()
        layout.addRow("Marca:", self._equip_brand)

        self._equip_model = QLabel()
        layout.addRow("Modelo:", self._equip_model)

        self._equip_serial = QLabel()
        layout.addRow("Nº Serie:", self._equip_serial)

        self._equip_color = QLabel()
        layout.addRow("Color:", self._equip_color)

        self._equip_os = QLabel()
        layout.addRow("Sistema operativo:", self._equip_os)

        self._equip_accessories = QLabel()
        self._equip_accessories.setWordWrap(True)
        layout.addRow("Accesorios:", self._equip_accessories)

        self._equip_physical = QTextEdit()
        self._equip_physical.setReadOnly(True)
        self._equip_physical.setMaximumHeight(60)
        layout.addRow("Estado físico:", self._equip_physical)

        return tab

    def _create_diagnosis_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Diagnóstico
        layout.addWidget(QLabel("<b>Diagnóstico técnico:</b>"))
        self._editor_diagnosis = RichTextEdit()
        self._editor_diagnosis.setMinimumHeight(150)
        layout.addWidget(self._editor_diagnosis)

        # Trabajo realizado
        layout.addWidget(QLabel("<b>Trabajo realizado:</b>"))
        self._editor_work = RichTextEdit()
        self._editor_work.setMinimumHeight(150)
        layout.addWidget(self._editor_work)

        # Recomendaciones
        layout.addWidget(QLabel("<b>Recomendaciones al cliente:</b>"))
        self._editor_recommendations = RichTextEdit()
        self._editor_recommendations.setMinimumHeight(150)
        layout.addWidget(self._editor_recommendations)

        # Botón guardar
        self._btn_save_editors = QPushButton("Guardar diagnóstico")
        self._btn_save_editors.clicked.connect(self._save_diagnosis)
        layout.addWidget(self._btn_save_editors)

        return tab

    def _create_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self._history_timeline = HistoryTimeline(self._order) if self._order else QLabel("Sin orden")
        layout.addWidget(self._history_timeline)
        return tab

    def _load_order(self) -> None:
        self._order = self._order_service.get_by_id(self._order_id)
        if not self._order:
            QMessageBox.warning(self, "Error", "No se encontró la orden.")
            return

        order = self._order
        customer = order.customer
        equipment = order.equipment

        # Summary
        self._lbl_order_number.setText(order.order_number)
        self._lbl_status.setText(order.status)
        self._lbl_priority.setText(order.priority)
        self._lbl_customer.setText(customer.full_name if customer else "")
        self._lbl_phone.setText(customer.phone_primary if customer else "")
        self._lbl_equipment_type.setText(equipment.equipment_type if equipment else "")
        self._lbl_brand.setText(equipment.brand or "" if equipment else "")
        self._lbl_model.setText(equipment.model or "" if equipment else "")
        self._lbl_serial.setText(equipment.serial_number or "" if equipment else "")
        self._lbl_intake_date.setText(order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else "")
        self._lbl_estimated.setText(
            order.estimated_delivery_date.strftime("%Y-%m-%d") if order.estimated_delivery_date else "No definida"
        )
        self._lbl_balance.setText(f"${order.balance:,.2f}")
        self._lbl_technician.setText(order.technician or "No asignado")
        self._problem_display.setPlainText(order.reported_problem or "")

        # Customer
        if customer:
            self._cust_name.setText(customer.full_name)
            self._cust_id.setText(customer.id_number or "Sin identificación")
            self._cust_phone.setText(customer.phone_primary)
            self._cust_email.setText(customer.email or "No registrado")
            self._cust_address.setText(customer.address or "No registrada")

        # Equipment
        if equipment:
            self._equip_type.setText(equipment.equipment_type)
            self._equip_brand.setText(equipment.brand or "No especificada")
            self._equip_model.setText(equipment.model or "No especificado")
            self._equip_serial.setText(equipment.serial_number or "No registrado")
            self._equip_color.setText(equipment.color or "No especificado")
            self._equip_os.setText(equipment.os or "No especificado")
            self._equip_accessories.setText(equipment.accessories or "Sin accesorios")
            self._equip_physical.setPlainText(equipment.physical_state or "")

        # Load diagnosis
        if self._order.diagnosis_html:
            self._editor_diagnosis.set_html(self._order.diagnosis_html)
        if self._order.work_done_html:
            self._editor_work.set_html(self._order.work_done_html)
        if self._order.recommendations_html:
            self._editor_recommendations.set_html(self._order.recommendations_html)

        # Set up photo tab
        photo_tab = PhotoTab(self._order_id, order.order_number, self)
        idx = self._tabs.indexOf(self._photo_tab)
        self._tabs.removeTab(idx)
        self._tabs.insertTab(idx, photo_tab, "Fotografías")
        self._photo_tab = photo_tab

        # Refresh history
        if hasattr(self, '_history_timeline') and self._history_timeline:
            self._history_timeline._load_history()

    def _save_diagnosis(self) -> None:
        """Guardar diagnóstico, trabajo y recomendaciones."""
        if not self._order:
            return
        self._order.diagnosis_html = self._editor_diagnosis.to_html()
        self._order.work_done_html = self._editor_work.to_html()
        self._order.recommendations_html = self._editor_recommendations.to_html()
        self._order_service.order_repo.update(self._order)
        self._order_service.add_event(
            self._order, "Diagnóstico actualizado", "Diagnóstico guardado",
            f"Diagnóstico: {len(self._order.diagnosis_html or '')} chars"
        )
        QMessageBox.information(self, "Guardado", "Diagnóstico guardado exitosamente.")
        logger.info("Diagnóstico guardado para orden %s", self._order.order_number)

        # Refresh history tab
        if hasattr(self, '_history_timeline') and self._history_timeline:
            self._history_timeline._load_history()

    def _change_status(self) -> None:
        if not self._order:
            return

        from PyQt6.QtWidgets import QInputDialog

        status, ok = QInputDialog.getItem(
            self,
            "Cambiar estado",
            "Nuevo estado:",
            ORDER_STATUSES,
            ORDER_STATUSES.index(self._order.status) if self._order.status in ORDER_STATUSES else 0,
            False,
        )
        if ok and status:
            self._order = self._order_service.change_status(self._order, status)
            self._load_order()
            logger.info("Estado cambiado a %s para orden %s", status, self._order.order_number)
