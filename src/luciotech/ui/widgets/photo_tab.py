"""Pestaña de fotografías para la vista de orden."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QFileDialog,
    QInputDialog,
)

from luciotech.database.models import Photo
from luciotech.services.image_service import PhotoService
from luciotech.config import PHOTO_TYPES

logger = logging.getLogger(__name__)


class PhotoTab(QWidget):
    """Pestaña de gestión de fotografías."""

    def __init__(self, order_id: int, order_number: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_id = order_id
        self._order_number = order_number
        self._photo_service = PhotoService()
        self._photos: list[Photo] = []
        self._init_ui()
        self._load_photos()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra superior
        toolbar = QHBoxLayout()
        self._btn_add = QPushButton("➕ Añadir fotografías")
        self._btn_add.clicked.connect(self._add_photos)
        toolbar.addWidget(self._btn_add)

        self._btn_add_folder = QPushButton("📁 Desde carpeta")
        self._btn_add_folder.clicked.connect(self._add_from_folder)
        toolbar.addWidget(self._btn_add_folder)

        self._btn_delete = QPushButton("🗑 Eliminar")
        self._btn_delete.clicked.connect(self._delete_selected)
        toolbar.addWidget(self._btn_delete)

        self._btn_rotate = QPushButton("🔄 Rotar")
        self._btn_rotate.clicked.connect(self._rotate_selected)
        toolbar.addWidget(self._btn_rotate)

        self._btn_move_up = QPushButton("⬆ Subir")
        self._btn_move_up.clicked.connect(self._move_selected_up)
        toolbar.addWidget(self._btn_move_up)

        self._btn_move_down = QPushButton("⬇ Bajar")
        self._btn_move_down.clicked.connect(self._move_selected_down)
        toolbar.addWidget(self._btn_move_down)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Splitter: lista + preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Lista de fotos
        list_group = QGroupBox("Fotografías")
        list_layout = QVBoxLayout(list_group)

        self._list = QListWidget()
        self._list.setIconSize(QSize(100, 100))
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setSpacing(8)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.itemDoubleClicked.connect(self._open_full_size)
        list_layout.addWidget(self._list)

        splitter.addWidget(list_group)

        # Panel de detalles
        detail_group = QGroupBox("Detalles")
        detail_layout = QVBoxLayout(detail_group)

        detail_layout.addWidget(QLabel("Tipo:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(PHOTO_TYPES)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        detail_layout.addWidget(self._type_combo)

        detail_layout.addWidget(QLabel("Descripción:"))
        self._desc_input = QLineEdit()
        self._desc_input.textChanged.connect(self._on_desc_changed)
        detail_layout.addWidget(self._desc_input)

        detail_layout.addStretch()

        # Preview grande
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet("background: #333; min-height: 200px;")
        detail_layout.addWidget(self._preview_label)

        splitter.addWidget(detail_group)
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)

        self._list.currentItemChanged.connect(self._on_selection_changed)

    def _load_photos(self) -> None:
        self._list.clear()
        self._photos = self._photo_service.get_photos(self._order_id)

        for photo in self._photos:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, photo)

            # Cargar miniatura
            thumb_path = self._photo_service.image_service.get_thumbnail_path(photo.file_path)
            if thumb_path:
                pixmap = QPixmap(thumb_path)
                item.setIcon(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

            item.setText(f"{photo.photo_type}\n{photo.description or ''}")
            self._list.addItem(item)

    def _add_photos(self) -> None:
        """Seleccionar fotos desde el disco."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar fotografías",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if paths:
            self._import_photos(paths)

    def _add_from_folder(self) -> None:
        """Importar desde una carpeta (simulando recepción desde celular)."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta con fotografías"
        )
        if folder:
            from pathlib import Path
            p = Path(folder)
            paths = [str(f) for f in p.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}]
            if paths:
                self._import_photos(paths)

    def _import_photos(self, paths: list[str]) -> None:
        """Importar fotos a la orden."""
        photo_type, ok = QInputDialog.getItem(
            self, "Tipo de fotografía", "Tipo:",
            PHOTO_TYPES, 0, False,
        )
        if not ok:
            return

        photos = self._photo_service.add_photos(self._order_id, self._order_number, paths, photo_type)
        if photos:
            self._load_photos()
            QMessageBox.information(self, "Importadas", f"{len(photos)} fotografía(s) añadidas.")
        else:
            QMessageBox.warning(self, "Error", "No se pudieron importar las fotografías.")

    def _delete_selected(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        reply = QMessageBox.question(
            self, "Eliminar", f"¿Eliminar {len(items)} fotografía(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for item in items:
                photo: Photo = item.data(Qt.ItemDataRole.UserRole)
                self._photo_service.delete_photo(photo)
            self._load_photos()

    def _rotate_selected(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        for item in items:
            photo: Photo = item.data(Qt.ItemDataRole.UserRole)
            self._photo_service.rotate_photo(photo, 90)
        self._load_photos()

    def _move_selected_up(self) -> None:
        """Mover la foto seleccionada una posición hacia arriba."""
        current = self._list.currentItem()
        if not current:
            return
        row = self._list.row(current)
        if row <= 0:
            return
        self._swap_photos(row, row - 1)
        self._list.setCurrentRow(row - 1)

    def _move_selected_down(self) -> None:
        """Mover la foto seleccionada una posición hacia abajo."""
        current = self._list.currentItem()
        if not current:
            return
        row = self._list.row(current)
        if row >= self._list.count() - 1:
            return
        self._swap_photos(row, row + 1)
        self._list.setCurrentRow(row + 1)

    def _swap_photos(self, index_a: int, index_b: int) -> None:
        """Intercambiar el sort_order de dos fotos por sus índices en la lista."""
        if index_a == index_b:
            return
        photo_a: Photo = self._list.item(index_a).data(Qt.ItemDataRole.UserRole)
        photo_b: Photo = self._list.item(index_b).data(Qt.ItemDataRole.UserRole)
        self._photo_service.reorder_photos([
            (photo_a.id, photo_b.sort_order),
            (photo_b.id, photo_a.sort_order),
        ])
        self._load_photos()

    def _open_full_size(self, item: QListWidgetItem) -> None:
        photo: Photo = item.data(Qt.ItemDataRole.UserRole)
        pixmap = QPixmap(photo.file_path)
        if pixmap.isNull():
            return
        # Show in dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle(photo.file_name)
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        lbl = QLabel()
        lbl.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def _on_selection_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if not current:
            return
        photo: Photo = current.data(Qt.ItemDataRole.UserRole)
        self._type_combo.blockSignals(True)
        self._type_combo.setCurrentText(photo.photo_type)
        self._type_combo.blockSignals(False)
        self._desc_input.blockSignals(True)
        self._desc_input.setText(photo.description or "")
        self._desc_input.blockSignals(False)

        # Preview
        pixmap = QPixmap(photo.file_path)
        self._preview_label.setPixmap(
            pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

    def _on_type_changed(self, text: str) -> None:
        current = self._list.currentItem()
        if not current:
            return
        photo: Photo = current.data(Qt.ItemDataRole.UserRole)
        photo.photo_type = text
        self._photo_service.session.commit()
        current.setText(f"{photo.photo_type}\n{photo.description or ''}")

    def _on_desc_changed(self, text: str) -> None:
        current = self._list.currentItem()
        if not current:
            return
        photo: Photo = current.data(Qt.ItemDataRole.UserRole)
        photo.description = text.strip() or None
        self._photo_service.session.commit()
        current.setText(f"{photo.photo_type}\n{photo.description or ''}")
