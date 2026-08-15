"""Diálogo de vista de una orden."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QDate
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
    QDoubleSpinBox,
    QDateEdit,
    QLineEdit,
    QDialogButtonBox,
    QInputDialog,
)

from luciotech.database.models import ServiceOrder
from luciotech.services.order_service import OrderService
from luciotech.config import ORDER_STATUSES, PRIORITIES
from luciotech.ui.widgets.rich_text_edit import RichTextEdit
from luciotech.ui.widgets.photo_tab import PhotoTab
from luciotech.ui.widgets.history_timeline import HistoryTimeline
from luciotech.ui.widgets.budget_payments_tab import BudgetPaymentsTab
from luciotech.reports.pdf_service import ReceiptPDFService, TechnicalReportPDFService

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

        # Tab: Presupuesto y Pagos
        self._budget_tab = QWidget()  # placeholder
        self._tabs.addTab(self._budget_tab, "Presupuesto y Pagos")

        layout.addWidget(self._tabs)

        # Botones
        button_layout = QHBoxLayout()
        self._btn_change_status = QPushButton("Cambiar estado")
        self._btn_change_status.clicked.connect(self._change_status)
        button_layout.addWidget(self._btn_change_status)

        self._btn_edit_data = QPushButton("✏️ Editar datos")
        self._btn_edit_data.clicked.connect(self._edit_general_data)
        button_layout.addWidget(self._btn_edit_data)

        self._btn_pdf_receipt = QPushButton("📄 Comprobante PDF")
        self._btn_pdf_receipt.clicked.connect(self._generate_receipt_pdf)
        button_layout.addWidget(self._btn_pdf_receipt)

        self._btn_pdf_report = QPushButton("📋 Informe Técnico PDF")
        self._btn_pdf_report.clicked.connect(self._generate_technical_report)
        button_layout.addWidget(self._btn_pdf_report)

        self._btn_print = QPushButton("🖨 Imprimir")
        self._btn_print.clicked.connect(self._print_order)
        button_layout.addWidget(self._btn_print)

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

        # Password / PIN with toggle
        password_row = QHBoxLayout()
        self._lbl_password = QLabel("••••••")
        self._lbl_password.setProperty("_actual_text", "")
        password_row.addWidget(self._lbl_password)
        self._btn_toggle_password = QPushButton("👁")
        self._btn_toggle_password.setCheckable(True)
        self._btn_toggle_password.setFixedWidth(36)
        self._btn_toggle_password.setToolTip("Mostrar / ocultar contraseña")
        self._btn_toggle_password.toggled.connect(self._toggle_password_visibility)
        password_row.addWidget(self._btn_toggle_password)
        password_row.addStretch()
        layout.addRow("Contraseña/PIN:", password_row)

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

            # Password / PIN
            actual = equipment.password or ""
            self._lbl_password.setProperty("_actual_text", actual)
            self._btn_toggle_password.setChecked(False)
            self._lbl_password.setText("••••••" if actual else "Sin contraseña")

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

        # Sustituir el marcador inicial por el historial de la orden cargada.
        history_layout = self._history_tab.layout()
        history_layout.removeWidget(self._history_timeline)
        self._history_timeline.deleteLater()
        self._history_timeline = HistoryTimeline(order, self._history_tab)
        history_layout.addWidget(self._history_timeline)

        # Set up budget tab
        budget_tab = BudgetPaymentsTab(self._order, self)
        idx = self._tabs.indexOf(self._budget_tab)
        self._tabs.removeTab(idx)
        self._tabs.insertTab(idx, budget_tab, "Presupuesto y Pagos")
        self._budget_tab = budget_tab

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
            # Auto-set completion / delivery dates based on new status
            self._auto_set_dates_for_status(status)
            self._load_order()
            logger.info("Estado cambiado a %s para orden %s", status, self._order.order_number)

    def _auto_set_dates_for_status(self, status: str) -> None:
        """Set completion_date or delivery_date automatically based on status."""
        if not self._order:
            return
        now = datetime.now()
        changed = False
        if status in ("Reparado", "Listo para entregar") and not self._order.completion_date:
            self._order.completion_date = now
            changed = True
        if status == "Entregado" and not self._order.delivery_date:
            self._order.delivery_date = now
            changed = True
        if changed:
            self._order_service.order_repo.update(self._order)

    def _toggle_password_visibility(self, checked: bool) -> None:
        """Toggle between masked and visible password display."""
        actual = self._lbl_password.property("_actual_text") or ""
        if checked:
            self._lbl_password.setText(actual if actual else "Sin contraseña")
            self._btn_toggle_password.setText("🔒")
        else:
            self._lbl_password.setText("••••••" if actual else "Sin contraseña")
            self._btn_toggle_password.setText("👁")

    def _edit_general_data(self) -> None:
        """Open a dialog to edit general order fields."""
        if not self._order:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar datos de la orden")
        dialog.setMinimumWidth(400)
        form = QFormLayout(dialog)

        # Status
        combo_status = QComboBox()
        combo_status.addItems(ORDER_STATUSES)
        if self._order.status in ORDER_STATUSES:
            combo_status.setCurrentText(self._order.status)
        form.addRow("Estado:", combo_status)

        # Priority
        combo_priority = QComboBox()
        combo_priority.addItems(PRIORITIES)
        if self._order.priority in PRIORITIES:
            combo_priority.setCurrentText(self._order.priority)
        form.addRow("Prioridad:", combo_priority)

        # Technician
        edit_technician = QLineEdit(self._order.technician or "")
        edit_technician.setPlaceholderText("Nombre del técnico")
        form.addRow("Técnico:", edit_technician)

        # Estimated delivery date
        date_estimated = QDateEdit()
        date_estimated.setCalendarPopup(True)
        date_estimated.setDisplayFormat("yyyy-MM-dd")
        if self._order.estimated_delivery_date:
            date_estimated.setDate(QDate(
                self._order.estimated_delivery_date.year,
                self._order.estimated_delivery_date.month,
                self._order.estimated_delivery_date.day,
            ))
        form.addRow("Fecha estimada:", date_estimated)

        # Diagnostic cost
        spin_cost = QDoubleSpinBox()
        spin_cost.setRange(0, 999999.99)
        spin_cost.setDecimals(2)
        spin_cost.setPrefix("$")
        spin_cost.setValue(self._order.diagnostic_cost or 0.0)
        form.addRow("Costo de diagnóstico:", spin_cost)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        old_status = self._order.status
        new_status = combo_status.currentText()

        # Apply changes
        self._order.priority = combo_priority.currentText()
        self._order.technician = edit_technician.text().strip() or None
        qdate = date_estimated.date()
        self._order.estimated_delivery_date = datetime(qdate.year(), qdate.month(), qdate.day())
        self._order.diagnostic_cost = spin_cost.value()

        # Handle status change (uses change_status for history tracking)
        if new_status != old_status:
            self._order = self._order_service.change_status(self._order, new_status)
            self._auto_set_dates_for_status(new_status)
        else:
            self._order_service.order_repo.update(self._order)

        self._order_service.add_event(
            self._order, "Datos editados", "Datos generales actualizados",
            f"Estado={new_status}, Prioridad={self._order.priority}, "
            f"Técnico={self._order.technician or 'N/A'}"
        )

        QMessageBox.information(self, "Guardado", "Datos de la orden actualizados.")
        logger.info("Datos generales editados para orden %s", self._order.order_number)
        self._load_order()

    def _generate_receipt_pdf(self) -> None:
        """Generar comprobante de recepción en PDF."""
        if not self._order:
            return
        try:
            path = ReceiptPDFService.generate(self._order)
            self._order_service.add_event(
                self._order, "Documento generado", "Comprobante de recepción PDF",
                f"Archivo: {Path(path).name}"
            )
            QMessageBox.information(self, "PDF generado", f"Comprobante guardado en:\n{path}")
            self._open_file(path)
        except Exception as e:
            logger.exception("Error generando comprobante PDF")
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {e}")

    def _generate_technical_report(self) -> None:
        """Generar informe técnico en PDF."""
        if not self._order:
            return
        try:
            path = TechnicalReportPDFService.generate(self._order)
            self._order_service.add_event(
                self._order, "Documento generado", "Informe técnico PDF",
                f"Archivo: {Path(path).name}"
            )
            QMessageBox.information(self, "PDF generado", f"Informe técnico guardado en:\n{path}")
            self._open_file(path)
        except Exception as e:
            logger.exception("Error generando informe técnico PDF")
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {e}")

    def _print_order(self) -> None:
        """Imprimir resumen de la orden."""
        from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
        from PyQt6.QtGui import QTextDocument

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Imprimir orden")
        if dialog.exec():
            doc = QTextDocument()
            doc.setHtml(self._build_printable_html())
            doc.print(printer)

    def _build_printable_html(self) -> str:
        """Generar HTML imprimible de la orden."""
        from html import escape
        from luciotech.services.settings_service import SettingsService

        order = self._order
        customer = order.customer
        equipment = order.equipment
        settings = SettingsService()
        workshop_name = escape(settings.get("workshop_name", "JL Mantenimiento"))
        currency = settings.get("currency", "USD").strip().upper() or "USD"
        currency_prefix = "$" if currency == "USD" else f"{escape(currency)} "

        def safe(value) -> str:
            return escape(str(value or ""))

        return f"""
        <html><head><meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; }}
            h1 {{ text-align: center; color: #1a1a2e; }}
            .section {{ margin: 10px 0; border-bottom: 1px solid #ccc; padding-bottom: 8px; }}
            .label {{ font-weight: bold; color: #555; }}
        </style></head><body>
        <h1>{workshop_name} — Orden {safe(order.order_number)}</h1>
        <div class="section">
            <p><span class="label">Estado:</span> {safe(order.status)} | <span class="label">Prioridad:</span> {safe(order.priority)}</p>
            <p><span class="label">Fecha de ingreso:</span> {order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else ""}</p>
        </div>
        <div class="section">
            <h3>Cliente</h3>
            <p><span class="label">Nombre:</span> {safe(customer.full_name if customer else "")}</p>
            <p><span class="label">Teléfono:</span> {safe(customer.phone_primary if customer else "")}</p>
        </div>
        <div class="section">
            <h3>Equipo</h3>
            <p><span class="label">Tipo:</span> {safe(equipment.equipment_type if equipment else "")}</p>
            <p><span class="label">Marca/Modelo:</span> {safe(equipment.brand if equipment else "")} {safe(equipment.model if equipment else "")}</p>
            <p><span class="label">Problema:</span> {safe(equipment.reported_problem if equipment else "")}</p>
        </div>
        <div class="section">
            <p><span class="label">Total:</span> {currency_prefix}{order.total:,.2f} | <span class="label">Saldo:</span> {currency_prefix}{order.balance:,.2f}</p>
        </div>
        </body></html>
        """

    @staticmethod
    def _open_file(path: str) -> None:
        """Abrir archivo PDF con la aplicación predeterminada."""
        import subprocess
        import sys
        import os
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])
