"""Widget de línea de tiempo para el historial de una orden."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QComboBox,
    QLineEdit,
    QInputDialog,
    QMessageBox,
    QMenu,
    QDialog,
    QFormLayout,
    QTextEdit,
    QDialogButtonBox,
)

from luciotech.database.models import ServiceOrder, StatusHistory, HistoryEvent
from luciotech.database.repositories import StatusHistoryRepo, HistoryEventRepo
from luciotech.database.connection import get_session
from luciotech.config import EVENT_TYPES

logger = logging.getLogger(__name__)


class HistoryTimeline(QWidget):
    """Línea de tiempo de eventos de una orden."""

    def __init__(self, order: ServiceOrder, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order = order
        self._session = get_session()
        self._status_repo = StatusHistoryRepo(self._session)
        self._event_repo = HistoryEventRepo(self._session)
        self._init_ui()
        self._load_history()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self._btn_add_note = QPushButton("📝 Añadir nota")
        self._btn_add_note.clicked.connect(self._add_note)
        toolbar.addWidget(self._btn_add_note)

        self._btn_add_event = QPushButton("📋 Añadir evento")
        self._btn_add_event.clicked.connect(self._add_event)
        toolbar.addWidget(self._btn_add_event)

        self._btn_refresh = QPushButton("🔄 Actualizar")
        self._btn_refresh.clicked.connect(self._load_history)
        toolbar.addWidget(self._btn_refresh)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Scroll area con timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._timeline_container = QWidget()
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setSpacing(0)
        self._timeline_layout.setContentsMargins(20, 10, 20, 10)

        scroll.setWidget(self._timeline_container)
        layout.addWidget(scroll)

    def _load_history(self) -> None:
        # Limpiar
        while self._timeline_layout.count():
            item = self._timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Obtener historial de estados
        status_records = self._status_repo.get_by_order(self._order.id)
        # Obtener eventos
        events = self._event_repo.get_by_order(self._order.id)

        # Combinar y ordenar por fecha
        all_items = []
        for s in status_records:
            all_items.append(("status", s))
        for e in events:
            all_items.append(("event", e))

        all_items.sort(key=lambda x: x[1].changed_at if hasattr(x[1], 'changed_at') else x[1].created_at, reverse=True)

        if not all_items:
            empty = QLabel("Sin eventos registrados")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: palette(mid); padding: 40px; font-size: 14px;")
            self._timeline_layout.addWidget(empty)
            return

        for item_type, item in all_items:
            widget = self._create_timeline_item(item_type, item)
            self._timeline_layout.addWidget(widget)

        self._timeline_layout.addStretch()

    def _create_timeline_item(self, item_type: str, item) -> QFrame:
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            """
            QFrame {
                background-color: palette(base);
                border-left: 4px solid;
                border-radius: 6px;
                padding: 10px;
                margin: 4px 0;
            }
            """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        # Fecha
        if item_type == "status":
            date_str = item.changed_at.strftime("%Y-%m-%d %H:%M")
            frame.setStyleSheet(frame.styleSheet() + "border-left-color: palette(highlight);")
            title = f"Estado: {item.previous_status} → {item.new_status}"
            subtitle = item.comment or ""
        else:
            date_str = item.created_at.strftime("%Y-%m-%d %H:%M")
            frame.setStyleSheet(frame.styleSheet() + "border-left-color: palette(link);")
            title = f"[{item.event_type}] {item.title}"
            subtitle = item.description or ""

        # Left column: date + content
        left_col = QVBoxLayout()
        date_label = QLabel(date_str)
        date_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        left_col.addWidget(date_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_col.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("font-size: 12px; color: palette(mid);")
            sub_label.setWordWrap(True)
            left_col.addWidget(sub_label)

        if hasattr(item, 'user') and item.user:
            user_label = QLabel(f"Por: {item.user}")
            user_label.setStyleSheet("font-size: 11px; font-style: italic; color: palette(mid);")
            left_col.addWidget(user_label)

        layout.addLayout(left_col, 1)

        # Context menu para eventos (editar / eliminar)
        if item_type == "event":
            frame.setProperty("_event_id", item.id)
            frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            frame.customContextMenuRequested.connect(
                lambda pos, ev=item: self._on_event_context_menu(ev, frame)
            )

        return frame

    def _add_note(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, "Añadir nota", "Nota interna:",
        )
        if ok and text.strip():
            self._event_repo.create(HistoryEvent(
                order_id=self._order.id,
                event_type="Nota interna",
                title="Nota interna",
                description=text.strip(),
            ))
            self._load_history()
            logger.info("Nota interna añadida a orden %s", self._order.order_number)

    def _add_event(self) -> None:
        event_type, ok = QInputDialog.getItem(
            self, "Añadir evento", "Tipo de evento:",
            EVENT_TYPES, 0, False,
        )
        if not ok:
            return

        title, ok = QInputDialog.getText(
            self, "Título del evento", "Título:",
        )
        if not ok or not title.strip():
            return

        description, ok = QInputDialog.getMultiLineText(
            self, "Descripción", "Descripción del evento:",
        )
        if ok:
            self._event_repo.create(HistoryEvent(
                order_id=self._order.id,
                event_type=event_type,
                title=title.strip(),
                description=description.strip() if description else None,
            ))
            self._load_history()
            logger.info("Evento '%s' añadido a orden %s", event_type, self._order.order_number)

    # ---- Context menu para eventos ----

    def _on_event_context_menu(self, event: HistoryEvent, frame: QFrame) -> None:
        """Mostrar menú contextual al hacer clic derecho sobre un evento."""
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Editar")
        edit_action.triggered.connect(lambda: self._edit_event(event))

        delete_action = menu.addAction("🗑️ Eliminar")
        delete_action.triggered.connect(lambda: self._delete_event(event))

        menu.exec(frame.mapToGlobal(frame.rect().center()))

    def _edit_event(self, event: HistoryEvent) -> None:
        """Abrir diálogo para editar un evento del historial."""
        # Recargar el evento desde la sesión para tener datos frescos
        fresh = self._session.get(HistoryEvent, event.id)
        if fresh is None:
            QMessageBox.warning(self, "Editar evento", "El evento ya no existe.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar evento")
        dialog.setMinimumWidth(420)
        form = QFormLayout(dialog)

        # Tipo de evento
        type_combo = QComboBox()
        type_combo.addItems(EVENT_TYPES)
        idx = type_combo.findText(fresh.event_type)
        if idx >= 0:
            type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de evento:", type_combo)

        # Título
        title_edit = QLineEdit(fresh.title or "")
        form.addRow("Título:", title_edit)

        # Descripción
        desc_edit = QTextEdit()
        desc_edit.setPlainText(fresh.description or "")
        desc_edit.setMinimumHeight(100)
        form.addRow("Descripción:", desc_edit)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_title = title_edit.text().strip()
        if not new_title:
            QMessageBox.warning(self, "Editar evento", "El título no puede estar vacío.")
            return

        fresh.event_type = type_combo.currentText()
        fresh.title = new_title
        fresh.description = desc_edit.toPlainText().strip() or None

        try:
            self._event_repo.update(fresh)
            self._load_history()
            logger.info("Evento %d editado en orden %s", fresh.id, self._order.order_number)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el evento:\n{e}")
            logger.error("Error editando evento %d: %s", fresh.id, e)

    def _delete_event(self, event: HistoryEvent) -> None:
        """Eliminar un evento del historial tras confirmación."""
        fresh = self._session.get(HistoryEvent, event.id)
        if fresh is None:
            QMessageBox.warning(self, "Eliminar evento", "El evento ya no existe.")
            self._load_history()
            return

        reply = QMessageBox.question(
            self,
            "Eliminar evento",
            f"¿Eliminar el evento \"{fresh.title}\"?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._event_repo.delete(fresh)
            self._load_history()
            logger.info("Evento %d eliminado de orden %s", fresh.id, self._order.order_number)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el evento:\n{e}")
            logger.error("Error eliminando evento %d: %s", fresh.id, e)
