"""Página de inventario de equipos."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
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

from luciotech.database.models import Equipment
from luciotech.services.order_service import EquipmentService
from luciotech.ui.dialogs.equipment_dialog import EquipmentEditDialog


class EquipmentPage(QWidget):
    """Inventario buscable de los equipos recibidos en el taller."""

    new_reception_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = EquipmentService()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._load_equipment)
        self._init_ui()
        self._load_equipment()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Equipos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 12px 0;")
        layout.addWidget(title)

        actions = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setPlaceholderText(
            "Buscar por cliente, tipo, marca, modelo, serie o problema..."
        )
        self._search_input.textChanged.connect(lambda: self._search_timer.start())
        actions.addWidget(self._search_input)

        self._btn_new_reception = QPushButton("Nueva recepción")
        self._btn_new_reception.clicked.connect(self.new_reception_requested.emit)
        actions.addWidget(self._btn_new_reception)

        self._btn_edit = QPushButton("Editar equipo")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_selected)
        actions.addWidget(self._btn_edit)

        self._btn_refresh = QPushButton("Actualizar")
        self._btn_refresh.clicked.connect(self._load_equipment)
        actions.addWidget(self._btn_refresh)
        layout.addLayout(actions)

        self._table = QTableWidget()
        self._table.setColumnCount(10)
        self._table.setHorizontalHeaderLabels(
            [
                "Cliente",
                "Teléfono",
                "Tipo",
                "Marca",
                "Modelo",
                "Número de serie",
                "Color",
                "Sistema operativo",
                "Problema reportado",
                "Registrado",
            ]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._update_actions)
        self._table.cellDoubleClicked.connect(self._edit_selected)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        self._count_label = QLabel()
        self._count_label.setStyleSheet("padding: 6px; color: palette(mid);")
        layout.addWidget(self._count_label)

    def _load_equipment(self) -> None:
        self._service.repo.session.expire_all()
        query = self._search_input.text().strip()
        equipment_list = self._service.search(query) if query else self._service.get_all()

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(equipment_list))
        for row, equipment in enumerate(equipment_list):
            customer = equipment.customer
            customer_item = QTableWidgetItem(customer.full_name if customer else "")
            customer_item.setData(Qt.ItemDataRole.UserRole, equipment)
            self._table.setItem(row, 0, customer_item)
            self._table.setItem(
                row, 1, QTableWidgetItem(customer.phone_primary if customer else "")
            )
            self._table.setItem(row, 2, QTableWidgetItem(equipment.equipment_type))
            self._table.setItem(row, 3, QTableWidgetItem(equipment.brand or ""))
            self._table.setItem(row, 4, QTableWidgetItem(equipment.model or ""))
            self._table.setItem(row, 5, QTableWidgetItem(equipment.serial_number or ""))
            self._table.setItem(row, 6, QTableWidgetItem(equipment.color or ""))
            self._table.setItem(row, 7, QTableWidgetItem(equipment.os or ""))
            self._table.setItem(
                row, 8, QTableWidgetItem(equipment.reported_problem or "")
            )
            created = equipment.created_at.strftime("%Y-%m-%d") if equipment.created_at else ""
            self._table.setItem(row, 9, QTableWidgetItem(created))

        self._table.setSortingEnabled(True)
        self._count_label.setText(f"{len(equipment_list)} equipo(s)")
        self._update_actions()

    def _selected_equipment(self) -> Equipment | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_actions(self) -> None:
        self._btn_edit.setEnabled(self._selected_equipment() is not None)

    def _edit_selected(self, *_args) -> None:
        equipment = self._selected_equipment()
        if equipment is None:
            return
        dialog = EquipmentEditDialog(equipment, self)
        if dialog.exec():
            self._load_equipment()
