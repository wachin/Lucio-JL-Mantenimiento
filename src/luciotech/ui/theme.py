"""Temas visuales compartidos por el arranque y Configuración."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


THEMES = {
    "Claro (sistema)": "",
    "Oscuro (Fusion)": "fusion_dark",
    "Claro (Fusion)": "fusion_light",
}


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Aplicar un tema conocido y restablecer correctamente la paleta."""
    theme_value = THEMES.get(theme_name, "")
    if theme_value == "fusion_dark":
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(palette)
    elif theme_value == "fusion_light":
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
    else:
        app.setStyle("")
        app.setPalette(app.style().standardPalette())
