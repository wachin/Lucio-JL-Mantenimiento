"""Editor de texto enriquecido con barra de herramientas tipo Word."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QIcon,
    QImage,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from luciotech.config import get_data_dir

logger = logging.getLogger(__name__)


class RichTextToolbar(QToolBar):
    """Barra de herramientas para el editor enriquecido."""

    def __init__(self, editor: RichTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self._font_size_blocked = False
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        # Fuente
        self._font_combo = QComboBox()
        self._font_combo.setEditable(True)
        families = QFontDatabase.families()
        self._font_combo.addItems(sorted(families))
        self._font_combo.setCurrentText("Arial")
        self._font_combo.setMinimumWidth(150)
        self.addWidget(self._font_combo)

        # Tamaño
        self._size_combo = QComboBox()
        self._size_combo.setEditable(True)
        for size in (8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72):
            self._size_combo.addItem(str(size))
        self._size_combo.setCurrentText("12")
        self._size_combo.setMinimumWidth(60)
        self.addWidget(self._size_combo)

        self.addSeparator()

        # Formato de texto
        self._add_action("B", "Negrita (Ctrl+B)", self._toggle_bold, "Ctrl+B")
        self._add_action("I", "Cursiva (Ctrl+I)", self._toggle_italic, "Ctrl+I")
        self._add_action("U", "Subrayado (Ctrl+U)", self._toggle_underline, "Ctrl+U")
        self._add_action("S", "Tachado", self._toggle_strike)

        self.addSeparator()

        # Colores
        self._btn_text_color = QPushButton("A")
        self._btn_text_color.setStyleSheet("color: red; font-weight: bold;")
        self._btn_text_color.setToolTip("Color del texto")
        self._btn_text_color.clicked.connect(self._set_text_color)
        self.addWidget(self._btn_text_color)

        self._btn_bg_color = QPushButton("BG")
        self._btn_bg_color.setToolTip("Color de fondo")
        self._btn_bg_color.clicked.connect(self._set_bg_color)
        self.addWidget(self._btn_bg_color)

        self.addSeparator()

        # Alineación
        self._add_action("≡", "Alinear izquierda", self._align_left)
        self._add_action("≡", "Centrar", self._align_center)
        self._add_action("≡", "Alinear derecha", self._align_right)
        self._add_action("≡", "Justificar", self._align_justify)

        self.addSeparator()

        # Listas
        self._add_action("• Lista", "Lista con viñetas", self._toggle_bullet_list)
        self._add_action("1. Lista", "Lista numerada", self._toggle_numbered_list)

        self.addSeparator()

        # Sangría
        self._add_action("→+", "Aumentar sangría", self._increase_indent)
        self._add_action("←-", "Disminuir sangría", self._decrease_indent)

        self.addSeparator()

        # Insertar
        self._add_action("Tabla", "Insertar tabla", self._insert_table)
        self._add_action("Imagen", "Insertar imagen", self._insert_image)
        self._add_action("—", "Línea horizontal", self._insert_hr)
        self._add_action("📝 Insertar plantilla", "Insertar plantilla de texto", self._insert_template)

        self.addSeparator()

        # Herramientas
        self._add_action("↶", "Deshacer (Ctrl+Z)", lambda: self._editor.undo(), "Ctrl+Z")
        self._add_action("↷", "Rehacer (Ctrl+Y)", lambda: self._editor.redo(), "Ctrl+Y")
        self._add_action("✂", "Cortar (Ctrl+X)", lambda: self._editor.cut(), "Ctrl+X")
        self._add_action("📋", "Copiar (Ctrl+C)", lambda: self._editor.copy(), "Ctrl+C")
        self._add_action("📄", "Pegar (Ctrl+V)", lambda: self._editor.paste(), "Ctrl+V")
        self._add_action("Texto plano", "Pegar como texto sin formato", self._paste_plain)

        self.addSeparator()

        self._add_action("🔍", "Buscar y reemplazar (Ctrl+H)", self._find_replace, "Ctrl+H")
        self._add_action("🧹", "Limpiar formato", self._clear_format)

        self.addSeparator()

        self._add_action("🖨", "Vista previa de impresión (Ctrl+Shift+P)", self._print_preview, "Ctrl+Shift+P")

        self.addSeparator()

        # Zoom
        btn_zoom_out = QPushButton("−")
        btn_zoom_out.setToolTip("Alejar (Ctrl+Rueda)")
        btn_zoom_out.setFixedWidth(30)
        btn_zoom_out.clicked.connect(lambda: self._editor.zoom_out(10))
        self.addWidget(btn_zoom_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(45)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self._zoom_label)

        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setToolTip("Acercar (Ctrl+Rueda)")
        btn_zoom_in.setFixedWidth(30)
        btn_zoom_in.clicked.connect(lambda: self._editor.zoom_in(10))
        self.addWidget(btn_zoom_in)

    def _add_action(self, text: str, tooltip: str, callback, shortcut: str | None = None) -> None:
        action = QAction(text, self)
        action.setToolTip(tooltip)
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(shortcut)
        self.addAction(action)

    def _connect_signals(self) -> None:
        self._font_combo.currentTextChanged.connect(self._change_font_family)
        self._size_combo.currentTextChanged.connect(self._change_font_size)

    def _change_font_family(self, family: str) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        self._editor.merge_current_char_format(fmt)

    def _change_font_size(self, size_str: str) -> None:
        if self._font_size_blocked:
            return
        try:
            size = int(size_str)
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            self._editor.merge_current_char_format(fmt)
        except ValueError:
            pass

    def _toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(
            QFont.Weight.Bold if not self._editor.fontWeight() == QFont.Weight.Bold else QFont.Weight.Normal
        )
        self._editor.merge_current_char_format(fmt)

    def _toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self._editor.fontItalic())
        self._editor.merge_current_char_format(fmt)

    def _toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self._editor.fontUnderline())
        self._editor.merge_current_char_format(fmt)

    def _toggle_strike(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self._editor.fontStrikeOut())
        self._editor.merge_current_char_format(fmt)

    def _set_text_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._editor.merge_current_char_format(fmt)

    def _set_bg_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self._editor.merge_current_char_format(fmt)

    def _align_left(self) -> None:
        self._editor.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def _align_center(self) -> None:
        self._editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _align_right(self) -> None:
        self._editor.setAlignment(Qt.AlignmentFlag.AlignRight)

    def _align_justify(self) -> None:
        self._editor.setAlignment(Qt.AlignmentFlag.AlignJustify)

    def _toggle_bullet_list(self) -> None:
        cursor = self._editor.textCursor()
        block_fmt = QTextListFormat()
        if cursor.currentList().format().style() == QTextListFormat.Style.ListDisc:
            block_fmt.setStyle(QTextListFormat.Style.ListEmpty)
        else:
            block_fmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(block_fmt)

    def _toggle_numbered_list(self) -> None:
        cursor = self._editor.textCursor()
        block_fmt = QTextListFormat()
        if cursor.currentList().format().style() == QTextListFormat.Style.ListDecimal:
            block_fmt.setStyle(QTextListFormat.Style.ListEmpty)
        else:
            block_fmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(block_fmt)

    def _increase_indent(self) -> None:
        self._editor.setIndentWidth(self._editor.indentWidth() + 20)

    def _decrease_indent(self) -> None:
        self._editor.setIndentWidth(max(0, self._editor.indentWidth() - 20))

    def _insert_table(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Insertar tabla")
        layout = QFormLayout(dialog)
        rows_spin = QSpinBox()
        rows_spin.setRange(1, 50)
        rows_spin.setValue(3)
        cols_spin = QSpinBox()
        cols_spin.setRange(1, 10)
        cols_spin.setValue(3)
        layout.addRow("Filas:", rows_spin)
        layout.addRow("Columnas:", cols_spin)
        btn = QPushButton("Insertar")
        btn.clicked.connect(dialog.accept)
        layout.addRow(btn)
        if dialog.exec():
            rows = rows_spin.value()
            cols = cols_spin.value()
            cursor = self._editor.textCursor()
            cursor.insertText("<br>")
            html = "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>"
            for r in range(rows):
                html += "<tr>"
                for c in range(cols):
                    html += "<td style='padding:4px; border:1px solid #ccc;'>Celda</td>"
                html += "</tr>"
            html += "</table><br>"
            cursor.insertHtml(html)

    def _insert_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Insertar imagen", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        if not path:
            return

        # Copy the image to the data directory so it doesn't break when the
        # original file is moved or deleted.
        try:
            img_dir = get_data_dir() / "editor_images"
            img_dir.mkdir(parents=True, exist_ok=True)
            src = Path(path)
            dest = img_dir / f"{uuid.uuid4().hex}{src.suffix}"
            shutil.copy2(path, dest)
            image_path = str(dest)
        except Exception:
            # Fall back to the original path if copying fails
            image_path = path

        cursor = self._editor.textCursor()
        cursor.insertHtml(f'<br><img src="{image_path}" width="400"><br>')

    def update_zoom_label(self, level: int) -> None:
        """Update the zoom percentage shown in the toolbar."""
        self._zoom_label.setText(f"{level}%")

    def _insert_hr(self) -> None:
        cursor = self._editor.textCursor()
        cursor.insertHtml("<hr>")

    def _insert_template(self) -> None:
        """Insertar plantilla de texto en la posición del cursor."""
        import json
        from PyQt6.QtWidgets import QInputDialog
        from luciotech.database.connection import get_session
        from luciotech.database.models import Settings

        # Cargar plantillas desde la configuración
        session = get_session()
        setting = session.query(Settings).filter(Settings.key == "text_templates").first()
        
        if not setting or not setting.value:
            QMessageBox.information(
                self, "Plantillas",
                "No hay plantillas configuradas. Ve a Configuración → Plantillas para añadir."
            )
            return

        try:
            templates = json.loads(setting.value)
        except json.JSONDecodeError:
            templates = []

        if not templates:
            QMessageBox.information(
                self, "Plantillas",
                "No hay plantillas configuradas. Ve a Configuración → Plantillas para añadir."
            )
            return

        # Mostrar diálogo para seleccionar plantilla
        template_names = [t.get("name", "Sin nombre") for t in templates]
        name, accepted = QInputDialog.getItem(
            self, "Insertar plantilla", "Seleccione una plantilla:",
            template_names, 0, False
        )

        if not accepted or not name:
            return

        # Encontrar la plantilla seleccionada
        template = next((t for t in templates if t.get("name") == name), None)
        if not template:
            return

        # Insertar el contenido HTML en la posición del cursor
        cursor = self._editor.textCursor()
        cursor.insertHtml(template.get("content", ""))

    def _paste_plain(self) -> None:
        self._editor.setAcceptRichText(False)
        self._editor.paste()
        self._editor.setAcceptRichText(True)

    def _find_replace(self) -> None:
        dialog = FindReplaceDialog(self._editor, self)
        dialog.exec()

    def _clear_format(self) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            cursor.mergeCharFormat(fmt)

    def _print_preview(self) -> None:
        from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer, self)
        dialog.paintRequested.connect(lambda p: self._editor.print(p))
        dialog.exec()


class FindReplaceDialog(QDialog):
    """Diálogo de buscar y reemplazar."""

    def __init__(self, editor: RichTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self.setWindowTitle("Buscar y reemplazar")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        self._find_input = QLineEdit()
        self._replace_input = QLineEdit()
        layout.addRow("Buscar:", self._find_input)
        layout.addRow("Reemplazar con:", self._replace_input)

        btn_layout = QHBoxLayout()
        btn_find = QPushButton("Buscar")
        btn_find.clicked.connect(self._find)
        btn_replace = QPushButton("Reemplazar")
        btn_replace.clicked.connect(self._replace)
        btn_replace_all = QPushButton("Reemplazar todo")
        btn_replace_all.clicked.connect(self._replace_all)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_find)
        btn_layout.addWidget(btn_replace)
        btn_layout.addWidget(btn_replace_all)
        btn_layout.addWidget(btn_close)
        layout.addRow(btn_layout)

    def _find(self) -> None:
        text = self._find_input.text()
        if not text:
            return
        found = self._editor.find(text)
        if not found:
            # Try from beginning
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            self._editor.find(text)

    def _replace(self) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self._replace_input.text())
            self._find()

    def _replace_all(self) -> None:
        find_text = self._find_input.text()
        replace_text = self._replace_input.text()
        if not find_text:
            return
        # Move to start
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._editor.setTextCursor(cursor)
        count = 0
        while self._editor.find(find_text):
            cursor = self._editor.textCursor()
            cursor.insertText(replace_text)
            count += 1
            if count > 10000:
                break
        self._editor.setTextCursor(self._editor.textCursor())


class RichTextEdit(QWidget):
    """Widget de editor enriquecido con barra de herramientas integrada."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._editor = QTextEditWithIndent(self)
        self._toolbar = RichTextToolbar(self._editor, self)
        self._zoom_level = 100  # percentage, range 50–300

        # Connect Ctrl+wheel zoom from the inner text edit
        self._editor.zoom_requested.connect(self._handle_zoom)

        layout.addWidget(self._toolbar)
        layout.addWidget(self._editor)

    # ── Zoom ──────────────────────────────────────────────────────────

    def _handle_zoom(self, steps: int) -> None:
        """Handle a zoom request (each step = 10 %)."""
        self._apply_zoom(self._zoom_level + steps * 10)

    def zoom_in(self, amount: int = 10) -> None:
        """Zoom in by *amount* percentage points."""
        self._apply_zoom(self._zoom_level + amount)

    def zoom_out(self, amount: int = 10) -> None:
        """Zoom out by *amount* percentage points."""
        self._apply_zoom(self._zoom_level - amount)

    def _apply_zoom(self, level: int) -> None:
        level = max(50, min(300, level))
        if level == self._zoom_level:
            return
        diff = level - self._zoom_level
        self._zoom_level = level
        if diff > 0:
            self._editor._inner.zoomIn(diff)
        else:
            self._editor._inner.zoomOut(abs(diff))
        self._toolbar.update_zoom_label(level)

    def to_html(self) -> str:
        return self._editor.toHtml()

    def set_html(self, html: str) -> None:
        self._editor.setHtml(html)

    def to_plain_text(self) -> str:
        return self._editor.toPlainText()

    # Delegate common methods to inner editor
    def undo(self): self._editor.undo()
    def redo(self): self._editor.redo()
    def cut(self): self._editor.cut()
    def copy(self): self._editor.copy()
    def paste(self): self._editor.paste()
    def setAcceptRichText(self, value: bool): self._editor.setAcceptRichText(value)
    def find(self, text: str) -> bool: return self._editor.find(text)
    def print(self, printer): self._editor.print(printer)
    def textCursor(self): return self._editor.textCursor()
    def setTextCursor(self, cursor): self._editor.setTextCursor(cursor)
    def setFontWeight(self, w): self._editor.setFontWeight(w)
    def fontWeight(self): return self._editor.fontWeight()
    def setFontItalic(self, v): self._editor.setFontItalic(v)
    def fontItalic(self): return self._editor.fontItalic()
    def setFontUnderline(self, v): self._editor.setFontUnderline(v)
    def fontUnderline(self): return self._editor.fontUnderline()
    def setFontStrikeOut(self, v): self._editor.setFontStrikeOut(v)
    def fontStrikeOut(self): return self._editor.fontStrikeOut()
    def setAlignment(self, flag): self._editor.setAlignment(flag)
    def setIndentWidth(self, v): self._editor.setIndentWidth(v)
    def indentWidth(self): return self._editor.indentWidth() if hasattr(self._editor, 'indentWidth') else 0


class QTextEditWithIndent(QWidget):
    """QTextEdit con soporte de sangría."""

    zoom_requested = pyqtSignal(int)  # positive = zoom in, negative = zoom out

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PyQt6.QtWidgets import QTextEdit
        self._inner = QTextEdit()
        self._inner.installEventFilter(self)
        self._indent_width = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._inner)

    def eventFilter(self, obj, event):
        """Intercept Ctrl+MouseWheel on the inner QTextEdit for zoom."""
        from PyQt6.QtCore import QEvent
        if obj is self._inner and event.type() == QEvent.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                delta = 1 if event.angleDelta().y() > 0 else -1
                self.zoom_requested.emit(delta)
                return True
        return super().eventFilter(obj, event)

    def toHtml(self) -> str: return self._inner.toHtml()
    def setHtml(self, html: str) -> None: self._inner.setHtml(html)
    def toPlainText(self) -> str: return self._inner.toPlainText()
    def undo(self): self._inner.undo()
    def redo(self): self._inner.redo()
    def cut(self): self._inner.cut()
    def copy(self): self._inner.copy()
    def paste(self): self._inner.paste()
    def setAcceptRichText(self, v: bool): self._inner.setAcceptRichText(v)
    def find(self, text: str) -> bool: return self._inner.find(text)
    def print(self, printer): self._inner.print(printer)
    def textCursor(self): return self._inner.textCursor()
    def setTextCursor(self, cursor): self._inner.setTextCursor(cursor)
    def setFontWeight(self, w): self._inner.setFontWeight(w)
    def fontWeight(self): return self._inner.fontWeight()
    def setFontItalic(self, v): self._inner.setFontItalic(v)
    def fontItalic(self): return self._inner.fontItalic()
    def setFontUnderline(self, v): self._inner.setFontUnderline(v)
    def fontUnderline(self): return self._inner.fontUnderline()
    def setFontStrikeOut(self, v): self._inner.setFontStrikeOut(v)
    def fontStrikeOut(self): return self._inner.fontStrikeOut()
    def setAlignment(self, flag): self._inner.setAlignment(flag)
    def setIndentWidth(self, v): self._indent_width = v
    def indentWidth(self): return self._indent_width
    def merge_current_char_format(self, fmt):
        cursor = self._inner.textCursor()
        cursor.mergeCharFormat(fmt)

    def zoom_in(self, amount: int = 10) -> None:
        """Request zoom in; each 10 units = 1 step."""
        self.zoom_requested.emit(max(1, amount // 10))

    def zoom_out(self, amount: int = 10) -> None:
        """Request zoom out; each 10 units = 1 step."""
        self.zoom_requested.emit(-max(1, amount // 10))

    def paste(self) -> None:
        """Paste from clipboard, handling images by saving them to disk."""
        clipboard = QGuiApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            image = clipboard.image()
            if not image.isNull():
                try:
                    img_dir = get_data_dir() / "editor_images"
                    img_dir.mkdir(parents=True, exist_ok=True)
                    dest = img_dir / f"{uuid.uuid4().hex}.png"
                    if image.save(str(dest), "PNG"):
                        cursor = self._inner.textCursor()
                        cursor.insertHtml(
                            f'<br><img src="{dest}" width="400"><br>'
                        )
                        return
                except Exception:
                    logger.exception("Failed to paste clipboard image")
        # No image or save failed — fall back to default text paste
        self._inner.paste()
