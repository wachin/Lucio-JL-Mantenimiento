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

from luciotech.config import APP_NAME, ORDER_STATUSES
from luciotech.ui.pages.orders_page import OrdersPage
from luciotech.ui.pages.reception_page import ReceptionPage

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


class OrdersPage(PageBase):
    """Lista de órdenes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Órdenes de servicio", parent)


class ReceptionPage(PageBase):
    """Formulario de nueva recepción."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Nueva recepción", parent)


class CustomersPage(PageBase):
    """Gestión de clientes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Clientes", parent)


class EquipmentPage(PageBase):
    """Gestión de equipos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Equipos", parent)


class HistoryPage(PageBase):
    """Historial."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Historial", parent)


class ReportsPage(PageBase):
    """Reportes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Reportes", parent)


class BackupsPage(PageBase):
    """Copias de seguridad."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Copias de seguridad", parent)


class SettingsPage(PageBase):
    """Configuración."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Configuración", parent)


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
        self._pages["Equipos"] = EquipmentPage()
        self._pages["Historial"] = HistoryPage()
        self._pages["Reportes"] = ReportsPage()
        self._pages["Copias de seguridad"] = BackupsPage()
        self._pages["Configuración"] = SettingsPage()

        for page in self._pages.values():
            self._stack.addWidget(page)

        # Conectar señales
        self._orders_page.order_opened.connect(self._on_order_opened)
        self._reception_page.order_created.connect(self._on_order_created)

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
