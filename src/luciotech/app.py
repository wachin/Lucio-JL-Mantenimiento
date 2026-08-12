"""Configuración y creación de la aplicación Qt."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from luciotech.config import APP_NAME, get_data_dir, get_log_dir
from luciotech.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_application(argv: list[str] | None = None) -> QApplication:
    """Crear y configurar la aplicación Qt.

    Args:
        argv: Argumentos de línea de comandos (por defecto sys.argv).

    Returns:
        QApplication configurada con la ventana principal.
    """
    app = QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("LucioTech")

    # Configurar logging
    setup_logging(get_log_dir())
    logger.info("Aplicación iniciada")

    # Crear directorios necesarios
    _ensure_directories()

    # Crear y mostrar ventana principal
    from luciotech.ui.main_window import MainWindow
    from luciotech.database.connection import init_db

    init_db()
    window = MainWindow()
    window.show()

    return app


def _ensure_directories() -> None:
    """Crear directorios de datos si no existen."""
    dirs = [
        get_data_dir(),
        get_data_dir() / "attachments",
        get_data_dir() / "backups",
        get_log_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug("Directorio verificado: %s", d)
