"""Página de historial global del taller."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from luciotech.config import EVENT_TYPES
from luciotech.services.history_service import ActivityRecord, HistoryService


class HistoryPage(QWidget):
    """Actividad reciente de todas las órdenes de servicio."""

    order_opened = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = HistoryService()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.refresh)
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Historial global")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 12px 0;")
        layout.addWidget(title)

        filters = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setPlaceholderText(
            "Buscar por orden, cliente, equipo, estado, evento o detalle..."
        )
        self._search_input.textChanged.connect(lambda: self._search_timer.start())
        filters.addWidget(self._search_input)

        filters.addWidget(QLabel("Mostrar:"))
        self._category = QComboBox()
        self._category.addItems(["Todos", "Cambios de estado", "Eventos"])
        self._category.addItems(EVENT_TYPES)
        self._category.currentTextChanged.connect(self.refresh)
        filters.addWidget(self._category)

        self._btn_open = QPushButton("Abrir orden")
        self._btn_open.setEnabled(False)
        self._btn_open.clicked.connect(self._open_selected)
        filters.addWidget(self._btn_open)

        self._btn_refresh = QPushButton("Actualizar")
        self._btn_refresh.clicked.connect(self.refresh)
        filters.addWidget(self._btn_refresh)
        layout.addLayout(filters)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Fecha", "Tipo", "Nº Orden", "Cliente", "Equipo", "Detalle", "Usuario"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._update_actions)
        self._table.cellDoubleClicked.connect(self._open_selected)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        self._count_label = QLabel()
        self._count_label.setStyleSheet("padding: 6px; color: palette(mid);")
        layout.addWidget(self._count_label)

    def refresh(self, *_args) -> None:
        records = self._service.get_activity(
            query=self._search_input.text(),
            category=self._category.currentText(),
        )
        self._populate(records)

    def _populate(self, records: list[ActivityRecord]) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(records))
        for row, record in enumerate(records):
            date_item = QTableWidgetItem(record.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            date_item.setData(Qt.ItemDataRole.UserRole, record.order_id)
            self._table.setItem(row, 0, date_item)
            self._table.setItem(row, 1, QTableWidgetItem(record.category))
            self._table.setItem(row, 2, QTableWidgetItem(record.order_number))
            self._table.setItem(row, 3, QTableWidgetItem(record.customer_name))
            self._table.setItem(row, 4, QTableWidgetItem(record.equipment))
            detail_item = QTableWidgetItem(record.detail)
            detail_item.setToolTip(record.detail)
            self._table.setItem(row, 5, detail_item)
            self._table.setItem(row, 6, QTableWidgetItem(record.user))

        self._table.setSortingEnabled(True)
        self._count_label.setText(f"{len(records)} actividad(es)")
        self._update_actions()

    def _selected_order_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_actions(self) -> None:
        self._btn_open.setEnabled(self._selected_order_id() is not None)

    def _open_selected(self, *_args) -> None:
        order_id = self._selected_order_id()
        if order_id is not None:
            self.order_opened.emit(order_id)
