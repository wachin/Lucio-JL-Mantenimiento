"""Página de lista de órdenes de servicio."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QHeaderView,
    QCheckBox,
    QGroupBox,
    QDateEdit,
    QMessageBox,
    QMenu,
    QFileDialog,
)
from PyQt6.QtGui import QKeySequence

from luciotech.config import ORDER_STATUSES, PRIORITIES, get_data_dir
from luciotech.database.models import ServiceOrder
from luciotech.services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrdersPage(QWidget):
    """Página con lista avanzada de órdenes."""

    order_opened = pyqtSignal(int)  # order_id
    orders_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_service = OrderService()
        self._orders: list[ServiceOrder] = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_filters)
        self._column_labels = [
            "Nº Orden",
            "Fecha ingreso",
            "Cliente",
            "Teléfono",
            "Tipo equipo",
            "Marca",
            "Modelo",
            "Nº Serie",
            "Problema",
            "Estado",
            "Prioridad",
            "Total",
            "Saldo",
        ]
        self._column_config_path = get_data_dir() / "orders_columns.json"
        self._init_ui()
        self._restore_column_config()
        self._load_orders()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Texto libre: orden, cliente, equipo, serie...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)

        self._btn_new = QPushButton("Nueva recepción")
        self._btn_new.setShortcut("Ctrl+N")
        self._btn_new.clicked.connect(lambda: self.order_opened.emit(-1))  # -1 = nueva
        search_layout.addWidget(self._btn_new)

        self._btn_refresh = QPushButton("Actualizar")
        self._btn_refresh.clicked.connect(self._load_orders)
        search_layout.addWidget(self._btn_refresh)

        self._btn_columns = QPushButton("Columnas")
        self._btn_columns.setToolTip("Elegir columnas visibles")
        self._btn_columns.clicked.connect(lambda: self._show_column_menu())
        search_layout.addWidget(self._btn_columns)

        self._btn_export = QPushButton("Exportar")
        self._btn_export.setToolTip("Exportar resultados filtrados a CSV")
        self._btn_export.clicked.connect(self._export_to_csv)
        search_layout.addWidget(self._btn_export)

        self._chk_trash = QCheckBox("Ver papelera")
        self._chk_trash.setToolTip("Mostrar las órdenes eliminadas")
        self._chk_trash.toggled.connect(self._on_trash_toggled)
        search_layout.addWidget(self._chk_trash)

        layout.addLayout(search_layout)

        # Filtros avanzados
        filter_group = QGroupBox("Filtros avanzados")
        filter_layout = QHBoxLayout(filter_group)

        self._filter_status = QComboBox()
        self._filter_status.addItem("Todos los estados")
        for s in ORDER_STATUSES:
            self._filter_status.addItem(s)
        self._filter_status.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self._filter_status)

        self._filter_priority = QComboBox()
        self._filter_priority.addItem("Todas")
        for p in PRIORITIES:
            self._filter_priority.addItem(p)
        self._filter_priority.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Prioridad:"))
        filter_layout.addWidget(self._filter_priority)

        self._chk_balance = QCheckBox("Con saldo pendiente")
        self._chk_balance.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self._chk_balance)

        self._chk_overdue = QCheckBox("Retrasadas")
        self._chk_overdue.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self._chk_overdue)

        filter_layout.addWidget(QLabel("Desde:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("Hasta:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_to)

        self._btn_clear_filters = QPushButton("Limpiar filtros")
        self._btn_clear_filters.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self._btn_clear_filters)

        layout.addWidget(filter_group)

        # Tabla de órdenes
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._column_labels))
        self._table.setHorizontalHeaderLabels(self._column_labels)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        # Configurar headers
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu)
        header.sectionResized.connect(self._save_column_config)
        header.sectionMoved.connect(self._save_column_config)

        layout.addWidget(self._table)

        # Contador
        self._count_label = QLabel("0 órdenes")
        self._count_label.setStyleSheet("padding: 8px; font-size: 13px;")
        layout.addWidget(self._count_label)

    def _on_search_changed(self, text: str) -> None:
        self._search_timer.start(400)  # Debounce 400ms

    def _on_filter_changed(self) -> None:
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self._search_input.text().strip()
        status = self._filter_status.currentText()
        priority = self._filter_priority.currentText()
        has_balance = self._chk_balance.isChecked()
        is_overdue = self._chk_overdue.isChecked()

        date_from = None
        if self._date_from.date().isValid() and self._date_from.date().year() > 2000:
            date_from = datetime(
                self._date_from.date().year(),
                self._date_from.date().month(),
                self._date_from.date().day(),
            )

        date_to = None
        if self._date_to.date().isValid() and self._date_to.date().year() > 2000:
            date_to = datetime(
                self._date_to.date().year(),
                self._date_to.date().month(),
                self._date_to.date().day(),
                23, 59, 59,
            )

        status_filter = status if status != "Todos los estados" else ""
        priority_filter = priority if priority != "Todas" else ""

        self._orders = self._order_service.search(
            query_text=query,
            status=status_filter,
            priority=priority_filter,
            has_balance=has_balance,
            is_overdue=is_overdue,
            deleted_only=self._chk_trash.isChecked(),
            date_from=date_from,
            date_to=date_to,
        )
        self._populate_table()

    def _clear_filters(self) -> None:
        self._search_input.clear()
        self._filter_status.setCurrentIndex(0)
        self._filter_priority.setCurrentIndex(0)
        self._chk_balance.setChecked(False)
        self._chk_overdue.setChecked(False)
        self._load_orders()

    def _load_orders(self) -> None:
        self._order_service.session.expire_all()
        if self._chk_trash.isChecked():
            self._orders = self._order_service.get_deleted()
        else:
            self._orders = self._order_service.get_all()
        self._populate_table()

    def _on_trash_toggled(self, checked: bool) -> None:
        self._btn_new.setEnabled(not checked)
        self._apply_filters()

    def _populate_table(self) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        for row, order in enumerate(self._orders):
            self._table.insertRow(row)
            customer = order.customer
            equipment = order.equipment

            order_item = QTableWidgetItem(order.order_number)
            order_item.setData(Qt.ItemDataRole.UserRole, order)
            self._table.setItem(row, 0, order_item)
            self._table.setItem(row, 1, QTableWidgetItem(order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else ""))
            self._table.setItem(row, 2, QTableWidgetItem(customer.full_name if customer else ""))
            self._table.setItem(row, 3, QTableWidgetItem(customer.phone_primary if customer else ""))
            self._table.setItem(row, 4, QTableWidgetItem(equipment.equipment_type if equipment else ""))
            self._table.setItem(row, 5, QTableWidgetItem(equipment.brand or "" if equipment else ""))
            self._table.setItem(row, 6, QTableWidgetItem(equipment.model or "" if equipment else ""))
            self._table.setItem(row, 7, QTableWidgetItem(equipment.serial_number or "" if equipment else ""))
            self._table.setItem(row, 8, QTableWidgetItem((order.reported_problem or "")[:80]))
            self._table.setItem(row, 9, QTableWidgetItem(order.status))
            self._table.setItem(row, 10, QTableWidgetItem(order.priority))
            self._table.setItem(row, 11, QTableWidgetItem(f"${order.total:,.2f}"))
            self._table.setItem(row, 12, QTableWidgetItem(f"${order.balance:,.2f}"))

            # Color por estado
            status_color = self._get_status_color(order.status)
            if status_color:
                for col in range(13):
                    item = self._table.item(row, col)
                    if item:
                        item.setBackground(status_color)

        self._table.setSortingEnabled(True)
        location = " en la papelera" if self._chk_trash.isChecked() else ""
        self._count_label.setText(f"{len(self._orders)} órdenes{location}")

    def _get_status_color(self, status: str) -> Qt.GlobalColor | None:
        """Color visual para cada estado."""
        colors = {
            "Recibido": Qt.GlobalColor.cyan,
            "Pendiente de diagnóstico": Qt.GlobalColor.yellow,
            "Diagnosticado": Qt.GlobalColor.lightGray,
            "Esperando aprobación": Qt.GlobalColor.magenta,
            "Esperando repuesto": Qt.GlobalColor.darkYellow,
            "En reparación": Qt.GlobalColor.blue,
            "Reparado": Qt.GlobalColor.darkGreen,
            "Listo para entregar": Qt.GlobalColor.green,
            "Entregado": Qt.GlobalColor.gray,
            "No reparable": Qt.GlobalColor.red,
            "Cancelado": Qt.GlobalColor.darkGray,
        }
        return colors.get(status)

    def _on_double_click(self) -> None:
        row = self._table.currentRow()
        order = self._order_at_row(row)
        if order is not None:
            self.order_opened.emit(order.id)

    def _order_at_row(self, row: int) -> ServiceOrder | None:
        """Obtener la orden asociada a una fila incluso si la tabla se ordenó."""
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_context_menu(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        order = self._order_at_row(row)
        if order is None:
            return

        menu = QMenu(self)
        open_action = menu.addAction("Abrir orden")
        open_action.triggered.connect(lambda: self.order_opened.emit(order.id))

        menu.addSeparator()
        if self._chk_trash.isChecked():
            restore_action = menu.addAction("Restaurar orden")
            restore_action.triggered.connect(lambda: self._restore(order))

            menu.addSeparator()
            perm_delete_action = menu.addAction("🗑️ Eliminar definitivamente")
            perm_delete_action.triggered.connect(lambda: self._permanent_delete(order))
        else:
            delete_action = menu.addAction("Eliminar (papelera)")
            delete_action.triggered.connect(lambda: self._soft_delete(order))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _soft_delete(self, order: ServiceOrder) -> None:
        """Eliminar lógicamente una orden."""
        reply = QMessageBox.question(
            self,
            "Eliminar orden",
            f"¿Mover la orden {order.order_number} a la papelera?\nNo se eliminará permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._order_service.order_repo.soft_delete(order)
            self._load_orders()
            self.orders_changed.emit()
            logger.info("Orden eliminada (papelera): %s", order.order_number)

    def _restore(self, order: ServiceOrder) -> None:
        """Restaurar una orden eliminada."""
        reply = QMessageBox.question(
            self,
            "Restaurar orden",
            f"¿Restaurar la orden {order.order_number}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._order_service.restore(order)
            self._load_orders()
            self.orders_changed.emit()
            logger.info("Orden restaurada desde la papelera: %s", order.order_number)

    def _permanent_delete(self, order: ServiceOrder) -> None:
        """Eliminar definitivamente una orden y todos sus datos relacionados."""
        reply = QMessageBox.warning(
            self,
            "⚠️ Eliminar definitivamente",
            f"¿Está seguro de que desea ELIMINAR DEFINITIVAMENTE la orden "
            f"{order.order_number}?\n\n"
            f"Se borrarán permanentemente:\n"
            f"• Todas las fotos adjuntas\n"
            f"• Todos los pagos registrados\n"
            f"• Todo el historial de eventos\n"
            f"• Todo el historial de estados\n"
            f"• La orden completa\n\n"
            f"⚠️ Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._order_service.order_repo.permanent_delete(order)
                self._load_orders()
                self.orders_changed.emit()
                logger.info("Orden eliminada definitivamente: %s", order.order_number)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error al eliminar",
                    f"No se pudo eliminar la orden:\n{e}",
                )
                logger.error("Error eliminando orden %s: %s", order.order_number, e)

    def _on_header_context_menu(self, pos) -> None:
        """Mostrar menú para toggle visibilidad de columnas."""
        self._show_column_menu(pos)

    def _show_column_menu(self, pos=None) -> None:
        """Mostrar menú con checkboxes para toggle columnas."""
        menu = QMenu(self)
        header = self._table.horizontalHeader()
        
        for col_idx in range(self._table.columnCount()):
            label = self._column_labels[col_idx]
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(col_idx))
            action.toggled.connect(lambda checked, c=col_idx: self._toggle_column(c, checked))
        
        if pos is not None:
            menu.exec(header.viewport().mapToGlobal(pos))
        else:
            menu.exec(self._btn_columns.mapToGlobal(self._btn_columns.rect().bottomLeft()))

    def _toggle_column(self, col_idx: int, visible: bool) -> None:
        """Toggle visibilidad de una columna."""
        self._table.setColumnHidden(col_idx, not visible)
        self._save_column_config()

    def _save_column_config(self) -> None:
        """Guardar configuración de columnas (visibilidad, anchos, orden)."""
        header = self._table.horizontalHeader()
        config = {
            "hidden": [],
            "widths": {},
            "order": [],
        }
        
        # Guardar columnas ocultas
        for col_idx in range(self._table.columnCount()):
            if header.isSectionHidden(col_idx):
                config["hidden"].append(col_idx)
        
        # Guardar anchos
        for col_idx in range(self._table.columnCount()):
            width = header.sectionSize(col_idx)
            config["widths"][str(col_idx)] = width
        
        # Guardar orden visual
        for visual_idx in range(self._table.columnCount()):
            logical_idx = header.logicalIndex(visual_idx)
            config["order"].append(logical_idx)
        
        try:
            self._column_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._column_config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error guardando configuración de columnas: %s", e)

    def _restore_column_config(self) -> None:
        """Restaurar configuración de columnas."""
        if not self._column_config_path.exists():
            return
        
        try:
            with open(self._column_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error("Error cargando configuración de columnas: %s", e)
            return
        
        header = self._table.horizontalHeader()
        
        # Restaurar orden
        if "order" in config and len(config["order"]) == self._table.columnCount():
            for visual_idx, logical_idx in enumerate(config["order"]):
                current_visual = header.visualIndex(logical_idx)
                if current_visual != visual_idx:
                    header.moveSection(current_visual, visual_idx)
        
        # Restaurar anchos
        if "widths" in config:
            for col_idx_str, width in config["widths"].items():
                col_idx = int(col_idx_str)
                if 0 <= col_idx < self._table.columnCount():
                    self._table.setColumnWidth(col_idx, width)
        
        # Restaurar visibilidad
        if "hidden" in config:
            for col_idx in config["hidden"]:
                if 0 <= col_idx < self._table.columnCount():
                    self._table.setColumnHidden(col_idx, True)

    def _export_to_csv(self) -> None:
        """Exportar resultados filtrados a CSV."""
        if not self._orders:
            QMessageBox.information(self, "Exportar", "No hay órdenes para exportar.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a CSV",
            f"ordenes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        
        if not file_path:
            return
        
        try:
            header = self._table.horizontalHeader()
            visible_columns = []
            for col_idx in range(self._table.columnCount()):
                if not header.isSectionHidden(col_idx):
                    visible_columns.append(col_idx)
            
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                # Escribir encabezados (solo columnas visibles)
                headers = [self._column_labels[col_idx] for col_idx in visible_columns]
                writer.writerow(headers)
                
                # Escribir datos
                for order in self._orders:
                    row_data = []
                    customer = order.customer
                    equipment = order.equipment
                    
                    # Mapear columnas a datos
                    all_data = [
                        order.order_number,
                        order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else "",
                        customer.full_name if customer else "",
                        customer.phone_primary if customer else "",
                        equipment.equipment_type if equipment else "",
                        equipment.brand or "" if equipment else "",
                        equipment.model or "" if equipment else "",
                        equipment.serial_number or "" if equipment else "",
                        (order.reported_problem or "")[:80],
                        order.status,
                        order.priority,
                        f"${order.total:,.2f}",
                        f"${order.balance:,.2f}",
                    ]
                    
                    # Solo columnas visibles
                    for col_idx in visible_columns:
                        row_data.append(all_data[col_idx])
                    
                    writer.writerow(row_data)
            
            QMessageBox.information(
                self,
                "Exportación exitosa",
                f"Se exportaron {len(self._orders)} órdenes a:\n{file_path}",
            )
            logger.info("Órdenes exportadas a CSV: %s (%d órdenes)", file_path, len(self._orders))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo exportar a CSV:\n{str(e)}",
            )
            logger.error("Error exportando CSV: %s", e)

    def cleanup(self) -> None:
        """Cerrar la sesión de base de datos asociada a esta página."""
        try:
            self._order_service.session.close()
        except Exception:
            logger.exception("Error cerrando sesión de OrdersPage")
