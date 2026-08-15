"""Ventana principal de la aplicación."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDesktopServices, QUrl
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QStatusBar,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from luciotech.config import APP_NAME, get_data_dir
from luciotech.ui.pages.orders_page import OrdersPage
from luciotech.ui.pages.reception_page import ReceptionPage
from luciotech.ui.pages.reports_page import ReportsPage
from luciotech.ui.pages.customers_page import CustomersPage
from luciotech.ui.pages.equipment_page import EquipmentPage
from luciotech.ui.pages.history_page import HistoryPage
from luciotech.ui.pages.home_page import HomePage
from luciotech.ui.dialogs.settings_dialog import SettingsDialog
from luciotech.services.backup_service import BackupService

logger = logging.getLogger(__name__)


class Sidebar(QFrame):
    """Barra lateral colapsable."""

    SECTION_HOME = "Inicio"
    SECTION_ORDERS = "Órdenes de servicio"
    SECTION_RECEPTION = "Nueva recepción"
    SECTION_CUSTOMERS = "Clientes"
    SECTION_EQUIPMENT = "Equipos"
    SECTION_HISTORY = "Historial"
    SECTION_REPORTS = "Reportes"
    SECTION_BACKUPS = "Copias de seguridad"
    SECTION_SETTINGS = "Configuración"

    SECTIONS = [
        SECTION_HOME,
        SECTION_ORDERS,
        SECTION_RECEPTION,
        SECTION_CUSTOMERS,
        SECTION_EQUIPMENT,
        SECTION_HISTORY,
        SECTION_REPORTS,
        SECTION_BACKUPS,
        SECTION_SETTINGS,
    ]

    section_selected = None  # Will be a signal in full version

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False
        self._list: QListWidget | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setFixedWidth(220)
        self._list.setStyleSheet(
            """
            QListWidget {
                background-color: palette(window);
                border: none;
                font-size: 14px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QListWidget::item:hover:!selected {
                background-color: palette(light);
            }
            """
        )

        for section in self.SECTIONS:
            item = QListWidgetItem(section)
            item.setSizeHint(QSize(200, 40))
            item.setToolTip(f"Ir a {section}")
            self._list.addItem(item)

        self._list.currentRowChanged.connect(self._on_selection)
        layout.addWidget(self._list)

    def _on_selection(self, row: int) -> None:
        if 0 <= row < len(self.SECTIONS):
            section = self.SECTIONS[row]
            if self.section_selected:
                self.section_selected.emit(section)

    def get_list(self) -> QListWidget | None:
        return self._list

    def collapse(self) -> None:
        """Colapsar la barra a solo iconos."""
        if self._list:
            self._list.setFixedWidth(60)
            self._collapsed = True

    def expand(self) -> None:
        """Expandir la barra completa."""
        if self._list:
            self._list.setFixedWidth(220)
            self._collapsed = False


class BackupsPage(QWidget):
    """Página de copias de seguridad."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Copias de seguridad")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        self._btn_create = QPushButton("💾 Crear copia de seguridad")
        self._btn_create.clicked.connect(self._create_backup)
        btn_layout.addWidget(self._btn_create)

        self._btn_restore = QPushButton("📂 Restaurar copia")
        self._btn_restore.clicked.connect(self._restore_backup)
        btn_layout.addWidget(self._btn_restore)

        self._btn_open_folder = QPushButton("📂 Abrir carpeta de backups")
        self._btn_open_folder.clicked.connect(self._open_backup_folder)
        btn_layout.addWidget(self._btn_open_folder)
        layout.addLayout(btn_layout)

        info = QLabel(
            "Las copias de seguridad incluyen la base de datos, fotografías y configuración.\n"
            "Se guardan en formato ZIP comprimido."
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 20px; color: palette(mid);")
        layout.addWidget(info)

    def _create_backup(self) -> None:
        path = BackupService.create_backup(self)
        if path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Copia creada", f"Copia guardada en:\n{path}")

    def _restore_backup(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        if BackupService.restore_backup(self):
            QMessageBox.information(self, "Restaurada", "Copia restaurada. Reinicie la aplicación.")

    def _open_backup_folder(self) -> None:
        backup_dir = get_data_dir() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))


class SettingsPage(QWidget):
    """Página de configuración."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Configuración")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        self._btn_open = QPushButton("⚙ Abrir configuración")
        self._btn_open.setStyleSheet("font-size: 16px; padding: 10px 30px;")
        self._btn_open.clicked.connect(self._open_settings)
        layout.addWidget(self._btn_open)
        layout.setAlignment(self._btn_open, Qt.AlignmentFlag.AlignCenter)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.window())
        dialog.configuration_saved.connect(self.settings_changed.emit)
        dialog.exec()


class MainWindow(QMainWindow):
    """Ventana principal de JL Mantenimiento."""

    def __init__(self) -> None:
        super().__init__()
        self._pages: dict[str, QWidget] = {}
        self._stack: QStackedWidget | None = None
        self._sidebar: Sidebar | None = None
        self._splitter: QSplitter | None = None
        self._init_ui()
        self._restore_state()
        logger.info("Ventana principal creada")

    @staticmethod
    def _state_file() -> Path:
        return get_data_dir() / "window_state.json"

    def _restore_state(self) -> None:
        """Restaurar geometría, splitter y sección abierta."""
        state_path = self._state_file()
        if not state_path.exists():
            return
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            geo = state.get("geometry")
            if geo:
                self.setGeometry(*geo)
            sizes = state.get("splitter_sizes")
            if sizes and self._splitter:
                self._splitter.setSizes(sizes)
            section = state.get("section")
            if section and self._sidebar and self._sidebar.get_list():
                sections = Sidebar.SECTIONS
                if section in sections:
                    self._sidebar.get_list().setCurrentRow(sections.index(section))
            logger.info("Estado de ventana restaurado")
        except Exception:
            logger.exception("No se pudo restaurar el estado de la ventana")

    def _save_state(self) -> None:
        """Guardar geometría, splitter y sección abierta."""
        state: dict = {}
        geo = self.geometry()
        state["geometry"] = [geo.x(), geo.y(), geo.width(), geo.height()]
        if self._splitter:
            state["splitter_sizes"] = self._splitter.sizes()
        if self._sidebar and self._sidebar.get_list():
            row = self._sidebar.get_list().currentRow()
            if 0 <= row < len(Sidebar.SECTIONS):
                state["section"] = Sidebar.SECTIONS[row]
        try:
            path = self._state_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            logger.info("Estado de ventana guardado")
        except Exception:
            logger.exception("No se pudo guardar el estado de la ventana")

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_state()
        super().closeEvent(event)

    def _init_ui(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 700)
        self.resize(1366, 768)

        # Widget central con splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter = self._splitter

        # Barra lateral
        # Crear señal dinámicamente
        class SidebarWithSignal(Sidebar):
            section_selected = pyqtSignal(str)

        self._sidebar = SidebarWithSignal()
        self._sidebar.section_selected.connect(self._on_section_selected)
        splitter.addWidget(self._sidebar)

        # Stack de páginas
        self._stack = QStackedWidget()
        self._setup_pages()
        splitter.addWidget(self._stack)

        splitter.setSizes([220, 980])
        splitter.setHandleWidth(1)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

        # Barra de herramientas
        self._setup_toolbar()

        # Barra de estado
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("JL Mantenimiento — Listo")

    def _setup_pages(self) -> None:
        if self._stack is None:
            return
        self._home_page = HomePage()
        self._pages["Inicio"] = self._home_page
        self._orders_page = OrdersPage()
        self._pages["Órdenes de servicio"] = self._orders_page
        self._reception_page = ReceptionPage()
        self._pages["Nueva recepción"] = self._reception_page
        self._pages["Clientes"] = CustomersPage()
        self._equipment_page = EquipmentPage()
        self._pages["Equipos"] = self._equipment_page
        self._history_page = HistoryPage()
        self._pages["Historial"] = self._history_page
        self._pages["Reportes"] = ReportsPage()
        self._pages["Copias de seguridad"] = BackupsPage()
        self._settings_page = SettingsPage()
        self._pages["Configuración"] = self._settings_page

        for page in self._pages.values():
            self._stack.addWidget(page)

        # Conectar señales
        self._orders_page.order_opened.connect(self._on_order_opened)
        self._orders_page.orders_changed.connect(self._home_page.refresh)
        self._orders_page.orders_changed.connect(self._history_page.refresh)
        self._reception_page.order_created.connect(self._on_order_created)
        self._equipment_page.new_reception_requested.connect(
            lambda: self._on_order_opened(-1)
        )
        self._history_page.order_opened.connect(self._on_order_opened)
        self._home_page.order_opened.connect(self._on_order_opened)
        self._home_page.new_reception_requested.connect(
            lambda: self._on_order_opened(-1)
        )
        self._home_page.orders_requested.connect(self._show_orders)
        self._settings_page.settings_changed.connect(
            self._reception_page.refresh_settings
        )

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Acción nueva recepción
        new_action = QAction("Nueva recepción", self)
        new_action.setToolTip("Crear nueva recepción (Ctrl+N)")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self._on_order_opened(-1))
        toolbar.addAction(new_action)

        # Acción buscar
        search_action = QAction("Buscar", self)
        search_action.setToolTip("Buscar órdenes (Ctrl+F)")
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self._show_orders_search)
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # Acción imprimir
        print_action = QAction("Imprimir", self)
        print_action.setToolTip("Imprimir (Ctrl+P)")
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self._contextual_print)
        toolbar.addAction(print_action)

    def _on_section_selected(self, section: str) -> None:
        """Cambiar la página visible según la sección seleccionada."""
        if self._stack and section in self._pages:
            index = list(self._pages.keys()).index(section)
            self._stack.setCurrentIndex(index)
            if section == "Inicio":
                self._home_page.refresh()
            if section == "Historial":
                self._history_page.refresh()
            self.statusBar().showMessage(f"Sección: {section}")

    def _on_order_opened(self, order_id: int) -> None:
        """Abrir vista de orden o ir a nueva recepción."""
        if order_id < 0:
            # Ir a nueva recepción
            idx = list(self._pages.keys()).index("Nueva recepción")
            self._stack.setCurrentIndex(idx)
            if self._sidebar:
                self._sidebar.get_list().setCurrentRow(idx)
        else:
            from luciotech.ui.dialogs.order_view_dialog import OrderViewDialog
            dialog = OrderViewDialog(order_id, self)
            dialog.exec()
            self._orders_page._load_orders()
            self._history_page.refresh()
            self._home_page.refresh()

    def _on_order_created(self, order_id: int) -> None:
        """Actualizar lista de órdenes después de crear una."""
        self._orders_page._load_orders()
        # Ir a la sección de órdenes
        idx = list(self._pages.keys()).index("Órdenes de servicio")
        self._stack.setCurrentIndex(idx)
        if self._sidebar:
            self._sidebar.get_list().setCurrentRow(idx)
        self._home_page.refresh()
        self._history_page.refresh()

    def _show_orders(self) -> None:
        """Ir al listado de órdenes."""
        idx = list(self._pages.keys()).index("Órdenes de servicio")
        self._stack.setCurrentIndex(idx)
        if self._sidebar:
            self._sidebar.get_list().setCurrentRow(idx)

    def _show_orders_search(self) -> None:
        """Abrir el listado y enfocar su buscador."""
        self._show_orders()
        self._orders_page._search_input.setFocus()
        self._orders_page._search_input.selectAll()

    def _contextual_print(self) -> None:
        """Imprimir según la página activa (Ctrl+P contextual)."""
        from PyQt6.QtWidgets import QMessageBox

        current = self._stack.currentWidget() if self._stack else None

        if isinstance(current, OrdersPage):
            row = current._table.currentRow()
            order = current._order_at_row(row)
            if order is None:
                QMessageBox.warning(
                    self, "Imprimir",
                    "Selecciona una orden de la tabla para imprimir.",
                )
                return
            try:
                from luciotech.reports.pdf_service import ReceiptPDFService
                pdf_path = ReceiptPDFService.generate(order)
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
                logger.info("Comprobante generado e imprimir: %s", pdf_path)
            except Exception:
                logger.exception("Error al generar comprobante para impresión")
                QMessageBox.critical(
                    self, "Error",
                    "No se pudo generar el comprobante de impresión.",
                )
            return

        QMessageBox.information(
            self, "Imprimir",
            "No hay nada para imprimir en esta vista.",
        )
