"""Pestaña de presupuesto y pagos para la vista de orden."""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QDateEdit,
)

from luciotech.database.models import ServiceOrder, Payment, BudgetConcept
from luciotech.database.repositories import BudgetConceptRepo
from luciotech.services.order_service import OrderService
from luciotech.config import PAYMENT_TYPES, PAYMENT_METHODS, CONCEPT_TYPES

logger = logging.getLogger(__name__)


class BudgetPaymentsTab(QWidget):
    """Pestaña de presupuesto y pagos."""

    def __init__(self, order: ServiceOrder, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order = order
        self._order_service = OrderService()
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Sección: Conceptos de presupuesto
        budget_group = QGroupBox("Presupuesto")
        budget_layout = QVBoxLayout(budget_group)

        # Tabla de conceptos
        self._concepts_table = QTableWidget()
        self._concepts_table.setColumnCount(5)
        self._concepts_table.setHorizontalHeaderLabels(["Tipo", "Descripción", "Cantidad", "Precio unit.", "Subtotal"])
        self._concepts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._concepts_table.setAlternatingRowColors(True)
        header = self._concepts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        budget_layout.addWidget(self._concepts_table)

        # Botones de conceptos
        concept_btn_layout = QHBoxLayout()
        self._btn_add_concept = QPushButton("➕ Añadir concepto")
        self._btn_add_concept.clicked.connect(self._add_concept_row)
        concept_btn_layout.addWidget(self._btn_add_concept)
        self._btn_remove_concept = QPushButton("🗑 Eliminar")
        self._btn_remove_concept.clicked.connect(self._remove_concept_row)
        concept_btn_layout.addWidget(self._btn_remove_concept)
        budget_layout.addLayout(concept_btn_layout)

        layout.addWidget(budget_group)

        # Resumen de costos
        summary_group = QGroupBox("Resumen de costos")
        summary_layout = QFormLayout(summary_group)

        self._lbl_subtotal = QLabel("$0.00")
        summary_layout.addRow("Subtotal:", self._lbl_subtotal)

        self._lbl_discount = QLabel("$0.00")
        summary_layout.addRow("Descuento:", self._lbl_discount)

        self._lbl_tax = QLabel("$0.00")
        summary_layout.addRow("Impuestos:", self._lbl_tax)

        summary_layout.addRow(HRLine())

        self._lbl_total = QLabel("$0.00")
        self._lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e;")
        summary_layout.addRow("TOTAL:", self._lbl_total)

        self._lbl_advance = QLabel("$0.00")
        summary_layout.addRow("Anticipo:", self._lbl_advance)

        self._lbl_paid = QLabel("$0.00")
        summary_layout.addRow("Pagado:", self._lbl_paid)

        self._lbl_balance = QLabel("$0.00")
        self._lbl_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        summary_layout.addRow("SALDO PENDIENTE:", self._lbl_balance)

        self._btn_recalc = QPushButton("Recalcular")
        self._btn_recalc.clicked.connect(self._recalculate)
        summary_layout.addRow("", self._btn_recalc)

        layout.addWidget(summary_group)

        # Sección: Pagos
        payments_group = QGroupBox("Pagos registrados")
        payments_layout = QVBoxLayout(payments_group)

        self._payments_table = QTableWidget()
        self._payments_table.setColumnCount(5)
        self._payments_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Método", "Monto", "Referencia"])
        self._payments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._payments_table.setAlternatingRowColors(True)
        payments_layout.addWidget(self._payments_table)

        # Botón registrar pago
        pay_btn_layout = QHBoxLayout()
        self._btn_add_payment = QPushButton("💵 Registrar pago")
        self._btn_add_payment.clicked.connect(self._register_payment)
        pay_btn_layout.addWidget(self._btn_add_payment)
        payments_layout.addLayout(pay_btn_layout)

        layout.addWidget(payments_group)

        # Botones finales
        final_layout = QHBoxLayout()
        self._btn_save_budget = QPushButton("💾 Guardar presupuesto")
        self._btn_save_budget.clicked.connect(self._save_budget)
        final_layout.addWidget(self._btn_save_budget)
        final_layout.addStretch()
        layout.addLayout(final_layout)

    def _load_data(self) -> None:
        """Cargar conceptos y pagos."""
        from luciotech.database.repositories import PaymentRepo
        from luciotech.database.connection import get_session

        session = get_session()
        pay_repo = PaymentRepo(session)
        payments = pay_repo.get_by_order(self._order.id)

        # Load persisted budget concepts
        concept_repo = BudgetConceptRepo(session)
        concepts = concept_repo.get_by_order(self._order.id)

        self._concepts_table.setRowCount(0)
        for concept in concepts:
            self._add_concept_row(
                concept_type=concept.concept_type,
                description=concept.description,
                quantity=concept.quantity,
                unit_price=concept.unit_price,
            )

        # Load payments
        self._payments_table.setRowCount(0)
        total_paid = 0
        for row, p in enumerate(payments):
            self._payments_table.insertRow(row)
            self._payments_table.setItem(row, 0, QTableWidgetItem(p.payment_date.strftime("%Y-%m-%d") if p.payment_date else ""))
            self._payments_table.setItem(row, 1, QTableWidgetItem(p.payment_type))
            self._payments_table.setItem(row, 2, QTableWidgetItem(p.payment_method))
            self._payments_table.setItem(row, 3, QTableWidgetItem(f"${p.amount:,.2f}"))
            self._payments_table.setItem(row, 4, QTableWidgetItem(p.reference or ""))
            total_paid += p.amount

        # Update summary
        self._recalculate()
        self._lbl_advance.setText(f"${self._order.advance_payment:,.2f}")
        self._lbl_paid.setText(f"${total_paid:,.2f}")
        self._lbl_balance.setText(f"${self._order.balance:,.2f}")

    def _add_concept_row(
        self,
        concept_type: str = "",
        description: str = "",
        quantity: float = 1.0,
        unit_price: float = 0.0,
    ) -> None:
        row = self._concepts_table.rowCount()
        self._concepts_table.insertRow(row)

        type_combo = QComboBox()
        type_combo.addItems(CONCEPT_TYPES)
        if concept_type and concept_type in CONCEPT_TYPES:
            type_combo.setCurrentText(concept_type)
        self._concepts_table.setCellWidget(row, 0, type_combo)

        desc_item = QTableWidgetItem(description)
        self._concepts_table.setItem(row, 1, desc_item)

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0, 9999)
        qty_spin.setValue(quantity)
        self._concepts_table.setCellWidget(row, 2, qty_spin)

        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999)
        price_spin.setPrefix("$ ")
        price_spin.setValue(unit_price)
        self._concepts_table.setCellWidget(row, 3, price_spin)

        subtotal_label = QLabel("$0.00")
        self._concepts_table.setCellWidget(row, 4, subtotal_label)

        def calc():
            sub = qty_spin.value() * price_spin.value()
            subtotal_label.setText(f"${sub:,.2f}")
        qty_spin.valueChanged.connect(calc)
        price_spin.valueChanged.connect(calc)
        calc()

    def _remove_concept_row(self) -> None:
        row = self._concepts_table.currentRow()
        if row >= 0:
            self._concepts_table.removeRow(row)

    def _recalculate(self) -> None:
        """Recalcular totales desde la tabla de conceptos."""
        subtotal = 0
        for row in range(self._concepts_table.rowCount()):
            sub_widget = self._concepts_table.cellWidget(row, 4)
            if sub_widget and isinstance(sub_widget, QLabel):
                text = sub_widget.text().replace("$", "").replace(",", "")
                try:
                    subtotal += float(text)
                except ValueError:
                    pass

        discount = self._order.discount
        tax = self._order.tax
        total = subtotal - discount + tax

        self._lbl_subtotal.setText(f"${subtotal:,.2f}")
        self._lbl_discount.setText(f"-${discount:,.2f}")
        self._lbl_tax.setText(f"${tax:,.2f}")
        self._lbl_total.setText(f"${total:,.2f}")

    def _register_payment(self) -> None:
        """Diálogo para registrar un pago."""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QLineEdit, QPushButton, QHBoxLayout, QDateEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar pago")
        dialog.setMinimumWidth(350)

        layout = QFormLayout(dialog)

        type_combo = QComboBox()
        type_combo.addItems(PAYMENT_TYPES)
        layout.addRow("Tipo de pago:", type_combo)

        method_combo = QComboBox()
        method_combo.addItems(PAYMENT_METHODS)
        layout.addRow("Método de pago:", method_combo)

        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.01, 999999)
        amount_spin.setPrefix("$ ")
        amount_spin.setValue(self._order.balance if self._order.balance > 0 else 0)
        layout.addRow("Monto:", amount_spin)

        ref_input = QLineEdit()
        ref_input.setPlaceholderText("Número de referencia, comprobante...")
        layout.addRow("Referencia:", ref_input)

        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Observaciones...")
        layout.addRow("Observaciones:", notes_input)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Registrar")
        btn_cancel = QPushButton("Cancelar")

        def do_save():
            try:
                payment = self._order_service.add_payment(
                    self._order,
                    type_combo.currentText(),
                    method_combo.currentText(),
                    amount_spin.value(),
                    ref_input.text(),
                    notes_input.text(),
                )
                QMessageBox.information(dialog, "Pago registrado", f"Pago de ${amount_spin.value():,.2f} registrado.")
                self._load_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))

        btn_save.clicked.connect(do_save)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

        dialog.exec()

    def _save_budget(self) -> None:
        """Guardar presupuesto calculado con conceptos persistentes."""
        from luciotech.database.connection import get_session
        from luciotech.database.repositories import PaymentRepo

        session = get_session()
        concept_repo = BudgetConceptRepo(session)

        concepts = []
        subtotal = 0.0
        for row in range(self._concepts_table.rowCount()):
            type_combo = self._concepts_table.cellWidget(row, 0)
            desc_item = self._concepts_table.item(row, 1)
            qty_spin = self._concepts_table.cellWidget(row, 2)
            price_spin = self._concepts_table.cellWidget(row, 3)

            if not (type_combo and qty_spin and price_spin):
                continue

            concept_type = type_combo.currentText()
            description = desc_item.text().strip() if desc_item else ""
            quantity = qty_spin.value()
            unit_price = price_spin.value()
            line_subtotal = quantity * unit_price
            subtotal += line_subtotal

            concepts.append(BudgetConcept(
                order_id=self._order.id,
                concept_type=concept_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=line_subtotal,
            ))

        concept_repo.replace_for_order(self._order.id, concepts)

        discount = self._order.discount
        tax = self._order.tax
        total = subtotal - discount + tax

        self._order.total = total
        total_paid = PaymentRepo(session).get_total_paid(self._order.id)
        self._order.balance = total - total_paid
        self._order_service.order_repo.update(self._order)

        self._recalculate()
        self._lbl_paid.setText(f"${total_paid:,.2f}")
        self._lbl_balance.setText(f"${self._order.balance:,.2f}")

        QMessageBox.information(self, "Guardado", f"Presupuesto guardado. Total: ${self._order.total:,.2f}")
        logger.info("Presupuesto guardado para orden %s: $%.2f (%d conceptos)",
                     self._order.order_number, self._order.total, len(concepts))


class HRLine(QWidget):
    """Línea horizontal separadora."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        from PyQt6.QtGui import QPalette
        self.setStyleSheet(f"background-color: {self.palette().color(QPalette.ColorRole.Mid).name()};")
