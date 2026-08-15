"""Diálogo de configuración de la aplicación."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QInputDialog,
)

from luciotech.config import (
    get_data_dir,
    EQUIPMENT_TYPES,
    ORDER_STATUSES,
    PRIORITIES,
    DEFAULT_CURRENCY,
    DEFAULT_ORDER_FORMAT,
)
from luciotech.database.connection import get_session
from luciotech.database.models import Settings
from luciotech.services.backup_service import BackupService
from luciotech.services.settings_service import SettingsService
from luciotech.ui.theme import THEMES, apply_theme

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Ventana de configuración organizada en categorías."""

    configuration_saved = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = get_session()
        self._settings: dict[str, str] = {}
        self._load_settings()
        self._init_ui()

    def _load_settings(self) -> None:
        """Cargar configuración desde la base de datos."""
        for s in self._session.query(Settings).all():
            self._settings[s.key] = s.value or ""

    def _get(self, key: str, default: str = "") -> str:
        return self._settings.get(key, default)

    def _set_setting(self, key: str, value: str) -> None:
        setting = self._session.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            self._session.add(setting)
        self._session.commit()
        self._settings[key] = value

    def _init_ui(self) -> None:
        self.setWindowTitle("Configuración")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Taller
        tabs.addTab(self._create_workshop_tab(), "Taller")
        # Técnico
        tabs.addTab(self._create_technician_tab(), "Técnico")
        # Costos
        tabs.addTab(self._create_costs_tab(), "Costos e impuestos")
        # Apariencia
        tabs.addTab(self._create_appearance_tab(), "Apariencia")
        # Catálogos
        tabs.addTab(self._create_catalogs_tab(), "Tipos de equipo")
        # Copias de seguridad
        tabs.addTab(self._create_backup_tab(), "Copias de seguridad")

        layout.addWidget(tabs)

        # Botones
        btn_layout = QHBoxLayout()
        self._btn_save = QPushButton("💾 Guardar")
        self._btn_save.clicked.connect(self._save_all)
        btn_layout.addWidget(self._btn_save)

        self._btn_reset = QPushButton("Restablecer")
        self._btn_reset.clicked.connect(self._reset_settings)
        btn_layout.addWidget(self._btn_reset)

        btn_layout.addStretch()
        self._btn_close = QPushButton("Cerrar")
        self._btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self._btn_close)

        layout.addLayout(btn_layout)

    def _create_workshop_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._workshop_name = QLineEdit(self._get("workshop_name", "JL Mantenimiento"))
        layout.addRow("Nombre del taller:", self._workshop_name)

        self._workshop_address = QLineEdit(self._get("workshop_address", ""))
        layout.addRow("Dirección:", self._workshop_address)

        self._workshop_phone = QLineEdit(self._get("workshop_phone", ""))
        layout.addRow("Teléfono:", self._workshop_phone)

        self._workshop_email = QLineEdit(self._get("workshop_email", ""))
        layout.addRow("Correo:", self._workshop_email)

        # Logo
        logo_layout = QHBoxLayout()
        self._logo_path = QLineEdit(self._get("logo_path", ""))
        self._logo_path.setReadOnly(True)
        logo_layout.addWidget(self._logo_path)
        self._btn_logo = QPushButton("Cargar logo")
        self._btn_logo.clicked.connect(self._load_logo)
        logo_layout.addWidget(self._btn_logo)
        layout.addRow("Logo:", logo_layout)

        return tab

    def _create_technician_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._tech_name = QLineEdit(self._get("technician_name", "Ing. Joseph Lucio"))
        layout.addRow("Nombre del técnico:", self._tech_name)

        self._tech_id = QLineEdit(self._get("technician_id", ""))
        layout.addRow("Identificación:", self._tech_id)

        self._order_format = QLineEdit(self._get("order_format", DEFAULT_ORDER_FORMAT))
        layout.addRow("Formato de orden:", self._order_format)

        self._warranty_days = QSpinBox()
        self._warranty_days.setRange(1, 365)
        self._warranty_days.setValue(int(self._get("warranty_days", "30")))
        layout.addRow("Días de garantía:", self._warranty_days)

        return tab

    def _create_costs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._currency = QLineEdit(self._get("currency", DEFAULT_CURRENCY))
        self._currency.setMaxLength(5)
        layout.addRow("Moneda:", self._currency)

        self._use_tax = QCheckBox("Usar impuestos")
        self._use_tax.setChecked(self._get("use_tax", "false") == "true")
        layout.addRow("", self._use_tax)

        self._tax_rate = QSpinBox()
        self._tax_rate.setRange(0, 100)
        self._tax_rate.setSuffix("%")
        self._tax_rate.setValue(int(self._get("tax_rate", "0")))
        layout.addRow("Tasa de impuesto:", self._tax_rate)

        return tab

    def _create_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(THEMES.keys())
        current_theme = self._get("theme", "Claro (sistema)")
        if current_theme in THEMES:
            self._theme_combo.setCurrentText(current_theme)
        layout.addRow("Tema visual:", self._theme_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(0, 24)
        self._font_size_spin.setSpecialValueText("Predeterminado")
        self._font_size_spin.setToolTip(
            "Tamaño de fuente de la interfaz. 0 = predeterminado del sistema."
        )
        current_font_size = int(self._get("font_size", "0"))
        self._font_size_spin.setValue(current_font_size)
        layout.addRow("Tamaño de fuente:", self._font_size_spin)

        return tab

    def _create_catalogs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Administre los tipos disponibles al registrar una recepción. "
            "Los equipos ya guardados no se modifican."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self._equipment_types = QListWidget()
        self._equipment_types.addItems(SettingsService().get_equipment_types())
        layout.addWidget(self._equipment_types)

        buttons = QHBoxLayout()
        add_button = QPushButton("Añadir tipo")
        add_button.clicked.connect(self._add_equipment_type)
        buttons.addWidget(add_button)
        remove_button = QPushButton("Eliminar seleccionado")
        remove_button.clicked.connect(self._remove_equipment_type)
        buttons.addWidget(remove_button)
        reset_button = QPushButton("Usar lista predeterminada")
        reset_button.clicked.connect(self._reset_equipment_types)
        buttons.addWidget(reset_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        return tab

    def _add_equipment_type(self) -> None:
        value, accepted = QInputDialog.getText(
            self, "Añadir tipo de equipo", "Nombre del tipo:"
        )
        value = value.strip()
        if not accepted or not value:
            return
        existing = {
            self._equipment_types.item(row).text().casefold()
            for row in range(self._equipment_types.count())
        }
        if value.casefold() in existing:
            QMessageBox.warning(self, "Tipo duplicado", "Ese tipo de equipo ya existe.")
            return
        self._equipment_types.addItem(value)

    def _remove_equipment_type(self) -> None:
        row = self._equipment_types.currentRow()
        if row >= 0:
            self._equipment_types.takeItem(row)

    def _reset_equipment_types(self) -> None:
        self._equipment_types.clear()
        self._equipment_types.addItems(EQUIPMENT_TYPES)

    def _create_backup_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Las copias de seguridad incluyen:\n"
            "• Base de datos completa\n"
            "• Todas las fotografías\n"
            "• Configuración\n\n"
            "Formato: archivo ZIP comprimido."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        self._btn_create_backup = QPushButton("💾 Crear copia de seguridad")
        self._btn_create_backup.clicked.connect(self._create_backup)
        btn_layout.addWidget(self._btn_create_backup)

        self._btn_restore_backup = QPushButton("📂 Restaurar copia")
        self._btn_restore_backup.clicked.connect(self._restore_backup)
        btn_layout.addWidget(self._btn_restore_backup)

        layout.addLayout(btn_layout)

        # Lista de copias recientes
        layout.addWidget(QLabel("Copias en el directorio de datos:"))
        self._backup_list = QLabel("—")
        self._backup_list.setWordWrap(True)
        layout.addWidget(self._backup_list)
        self._refresh_backup_list()

        return tab

    def _load_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path.setText(path)

    def _create_backup(self) -> None:
        path = BackupService.create_backup(self)
        if path:
            QMessageBox.information(self, "Copia creada", f"Copia de seguridad guardada en:\n{path}")
            self._refresh_backup_list()

    def _restore_backup(self) -> None:
        if BackupService.restore_backup(self):
            QMessageBox.information(self, "Restaurada", "Copia restaurada. Reinicie la aplicación para aplicar los cambios.")

    def _refresh_backup_list(self) -> None:
        backups = BackupService.list_backups()
        if backups:
            lines = []
            for b in backups[:5]:
                lines.append(f"• {b['name']} ({b['size_mb']:.1f} MB, {b['created_at'][:10]})")
            self._backup_list.setText("\n".join(lines))
        else:
            self._backup_list.setText("No hay copias de seguridad en el directorio de datos.")

    def _save_all(self) -> None:
        """Guardar toda la configuración."""
        order_format = self._order_format.text().strip()
        try:
            SettingsService.format_order_number(order_format, datetime.now(), 1)
        except ValueError as error:
            QMessageBox.warning(self, "Formato de orden inválido", str(error))
            return

        equipment_types = [
            self._equipment_types.item(row).text().strip()
            for row in range(self._equipment_types.count())
            if self._equipment_types.item(row).text().strip()
        ]
        if not equipment_types:
            QMessageBox.warning(
                self, "Tipos de equipo", "Debe conservar al menos un tipo de equipo."
            )
            return

        self._set_setting("workshop_name", self._workshop_name.text())
        self._set_setting("workshop_address", self._workshop_address.text())
        self._set_setting("workshop_phone", self._workshop_phone.text())
        self._set_setting("workshop_email", self._workshop_email.text())
        self._set_setting("logo_path", self._logo_path.text())
        self._set_setting("technician_name", self._tech_name.text())
        self._set_setting("technician_id", self._tech_id.text())
        self._set_setting("order_format", order_format)
        self._set_setting("warranty_days", str(self._warranty_days.value()))
        self._set_setting("currency", self._currency.text())
        self._set_setting("use_tax", "true" if self._use_tax.isChecked() else "false")
        self._set_setting("tax_rate", str(self._tax_rate.value()))
        self._set_setting("theme", self._theme_combo.currentText())
        self._set_setting("font_size", str(self._font_size_spin.value()))
        self._set_setting("equipment_types", json.dumps(equipment_types, ensure_ascii=False))

        QMessageBox.information(self, "Guardado", "Configuración guardada exitosamente.")
        logger.info("Configuración guardada")

        # Aplicar tema
        self._apply_theme()
        self.configuration_saved.emit()

    def _reset_settings(self) -> None:
        reply = QMessageBox.question(
            self, "Restablecer", "¿Restablecer toda la configuración a los valores predeterminados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._session.query(Settings).delete()
            self._session.commit()
            self._settings.clear()
            QMessageBox.information(self, "Restablecido", "Configuración restablecida. Reinicie la aplicación.")

    def _apply_theme(self) -> None:
        """Aplicar el tema visual seleccionado."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self._theme_combo.currentText())
