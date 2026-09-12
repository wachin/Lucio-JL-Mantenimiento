"""Temas visuales compartidos por el arranque y Configuración."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


THEMES = {
    "Claro (sistema)": "",
    "Oscuro (Fusion)": "fusion_dark",
    "Claro (Fusion)": "fusion_light",
}


def _windows_prefers_dark_mode() -> bool | None:
    """Read the Windows preference used by the system light/dark mode."""
    if sys.platform != "win32":
        return None

    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    except (FileNotFoundError, OSError):
        return None

    return value == 0


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Aplicar un tema conocido y restablecer correctamente la paleta."""
    theme_value = THEMES.get(theme_name, "")
    if theme_value == "":
        prefers_dark = _windows_prefers_dark_mode()
        if prefers_dark is True:
            theme_value = "fusion_dark"
        elif prefers_dark is False:
            theme_value = "fusion_light"

    if theme_value == "fusion_dark":
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Light, QColor(90, 90, 90))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(75, 75, 75))
        palette.setColor(QPalette.ColorRole.Mid, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.Dark, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            QColor(145, 145, 145),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(145, 145, 145),
        )
        app.setPalette(palette)
    elif theme_value == "fusion_light":
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
    else:
        app.setStyle("")
        app.setPalette(app.style().standardPalette())
