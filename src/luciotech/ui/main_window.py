"""Ventana principal de la aplicación."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
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

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

from luciotech.config import APP_NAME, ORDER_STATUSES
from luciotech.ui.pages.orders_page import OrdersPage
from luciotech.ui.pages.reception_page import ReceptionPage
from luciotech.ui.pages.reports_page import ReportsPage
from luciotech.ui.pages.customers_page import CustomersPage
from luciotech.ui.pages.equipment_page import EquipmentPage
from luciotech.ui.pages.history_page import HistoryPage
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


class PageBase(QWidget):
    """Página base para las secciones."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
            layout.addWidget(lbl)
        # Placeholder
        placeholder = QLabel("Contenido en desarrollo")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 16px; color: palette(mid); padding: 40px;")
        layout.addWidget(placeholder)


class HomePage(PageBase):
    """Panel de inicio con tarjetas informativas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Inicio", parent)


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


class SettingsPage(QWidget):
    """Página de configuración."""

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
        dialog.exec()


class MainWindow(QMainWindow):
    """Ventana principal de JL Mantenimiento."""

    def __init__(self) -> None:
        super().__init__()
        self._pages: dict[str, QWidget] = {}
        self._stack: QStackedWidget | None = None
        self._sidebar: Sidebar | None = None
        self._init_ui()
        logger.info("Ventana principal creada")

    def _init_ui(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 700)
        self.resize(1366, 768)

        # Widget central con splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Barra lateral
        from PyQt6.QtCore import pyqtSignal

        # Crear señal dinámicamente
        class SidebarWithSignal(Sidebar):
            from PyQt6.QtCore import pyqtSignal
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
        self._pages["Inicio"] = HomePage()
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
        self._pages["Configuración"] = SettingsPage()

        for page in self._pages.values():
            self._stack.addWidget(page)

        # Conectar señales
        self._orders_page.order_opened.connect(self._on_order_opened)
        self._reception_page.order_created.connect(self._on_order_created)
        self._equipment_page.new_reception_requested.connect(
            lambda: self._on_order_opened(-1)
        )
        self._history_page.order_opened.connect(self._on_order_opened)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Acción nueva recepción
        new_action = QAction("Nueva recepción", self)
        new_action.setToolTip("Crear nueva recepción (Ctrl+N)")
        new_action.setShortcut("Ctrl+N")
        toolbar.addAction(new_action)

        # Acción buscar
        search_action = QAction("Buscar", self)
        search_action.setToolTip("Buscar órdenes (Ctrl+F)")
        search_action.setShortcut("Ctrl+F")
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # Acción imprimir
        print_action = QAction("Imprimir", self)
        print_action.setToolTip("Imprimir (Ctrl+P)")
        print_action.setShortcut("Ctrl+P")
        toolbar.addAction(print_action)

    def _on_section_selected(self, section: str) -> None:
        """Cambiar la página visible según la sección seleccionada."""
        if self._stack and section in self._pages:
            index = list(self._pages.keys()).index(section)
            self._stack.setCurrentIndex(index)
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

    def _on_order_created(self, order_id: int) -> None:
        """Actualizar lista de órdenes después de crear una."""
        self._orders_page._load_orders()
        # Ir a la sección de órdenes
        idx = list(self._pages.keys()).index("Órdenes de servicio")
        self._stack.setCurrentIndex(idx)
        if self._sidebar:
            self._sidebar.get_list().setCurrentRow(idx)
