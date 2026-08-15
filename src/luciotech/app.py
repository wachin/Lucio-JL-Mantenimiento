"""Configuración y creación de la aplicación Qt."""

from __future__ import annotations

import logging
import sys
import tempfile
import traceback
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from luciotech.config import APP_NAME, get_data_dir, get_log_dir
from luciotech.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Manejador global de excepciones
# ---------------------------------------------------------------------------

def _global_exception_hook(exc_type, exc_value, exc_tb) -> None:
    """Capturar excepciones no manejadas de Python y mostrar un diálogo."""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("Excepción no manejada:\n%s", tb_text)

    # No mostrar diálogo para KeyboardInterrupt (Ctrl+C en consola)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    try:
        app = QApplication.instance()
        if app is not None:
            QMessageBox.critical(
                None,
                "Error inesperado",
                f"Ha ocurrido un error inesperado:\n\n{exc_value}\n\n"
                f"Se ha registrado el detalle en el log de la aplicación.",
            )
    except Exception:
        pass  # Si falla el diálogo, al menos ya se registró en el log

    sys.__excepthook__(exc_type, exc_value, exc_tb)


class _SafeQApplication(QApplication):
    """QApplication que captura excepciones en notify() (eventos Qt)."""

    def notify(self, receiver, event):  # noqa: ANN001
        try:
            return super().notify(receiver, event)
        except Exception as exc:
            tb_text = traceback.format_exc()
            logger.critical(
                "Excepción no manejada en evento Qt (%s -> %s):\n%s",
                type(receiver).__name__,
                type(event).__name__,
                tb_text,
            )
            try:
                QMessageBox.critical(
                    None,
                    "Error inesperado",
                    f"Ha ocurrido un error en la interfaz:\n\n{exc}\n\n"
                    f"Se ha registrado el detalle en el log de la aplicación.",
                )
            except Exception:
                pass
            return False


def _on_about_to_quit() -> None:
    """Registrar el cierre normal de la aplicación."""
    logger.info("Aplicación cerrada normalmente")


def create_application(argv: list[str] | None = None) -> QApplication:
    """Crear y configurar la aplicación Qt.

    Args:
        argv: Argumentos de línea de comandos (por defecto sys.argv).

    Returns:
        QApplication configurada con la ventana principal.
    """
    app = _SafeQApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("LucioTech")

    # Configurar logging
    setup_logging(get_log_dir())
    logger.info("Aplicación iniciada")

    # Instalar manejador global de excepciones Python
    sys.excepthook = _global_exception_hook

    # Registrar cierre normal de la aplicación
    app.aboutToQuit.connect(_on_about_to_quit)

    # Crear directorios necesarios
    _ensure_directories()

    # Crear y mostrar ventana principal
    from luciotech.ui.main_window import MainWindow
    from luciotech.database.connection import init_db
    from luciotech.services.settings_service import SettingsService
    from luciotech.ui.theme import apply_theme

    init_db()
    settings = SettingsService()
    apply_theme(app, settings.get("theme", "Claro (sistema)"))

    # Aplicar tamaño de fuente configurado
    font_size = settings.get_int("font_size", 0)
    if font_size > 0:
        from PyQt6.QtGui import QFont
        current_font = app.font()
        current_font.setPointSize(font_size)
        app.setFont(current_font)

    window = MainWindow()
    window.show()

    # QApplication does not take Python ownership of top-level widgets.  Keep a
    # strong reference for the whole application lifetime; otherwise ``window``
    # is destroyed when this function returns and Qt exits immediately because
    # there are no windows left.
    app.main_window = window  # type: ignore[attr-defined]

    # Ensure window is raised above other windows
    QTimer.singleShot(100, window.raise_)
    QTimer.singleShot(150, window.activateWindow)

    return app


def _is_dir_writable(path: Path) -> bool:
    """Check whether *path* (or its nearest existing ancestor) is writable."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        # Try creating a temporary file inside the directory
        test_file = path / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _ensure_directories() -> None:
    """Crear directorios de datos si no existen.

    Si el directorio de datos principal no es escribible se muestra una
    advertencia y se utiliza un directorio temporal como respaldo para que
    la aplicación pueda arrancar (útil en medios de solo lectura o permisos
    denegados).
    """
    data_dir = get_data_dir()
    log_dir = get_log_dir()

    if not _is_dir_writable(data_dir):
        fallback = Path(tempfile.mkdtemp(prefix="jlmtto-"))
        logger.warning(
            "El directorio de datos '%s' no es escribible. "
            "Usando directorio temporal: %s",
            data_dir,
            fallback,
        )
        try:
            QMessageBox.warning(
                None,
                "Directorio de datos no disponible",
                f"No se puede escribir en el directorio de datos:\n"
                f"{data_dir}\n\n"
                f"Se utilizará un directorio temporal en:\n"
                f"{fallback}\n\n"
                f"Los datos no se conservarán entre sesiones. "
                f"Verifique los permisos del directorio original.",
            )
        except Exception:
            pass  # Qt may not be ready; the log message is sufficient

        # Monkey-patch config helpers so the rest of the app uses the fallback
        import luciotech.config as _cfg

        _fallback_data = fallback
        _fallback_log = fallback / "logs"
        _cfg.get_data_dir = lambda: _fallback_data  # type: ignore[assignment]
        _cfg.get_log_dir = lambda: _fallback_log  # type: ignore[assignment]
        data_dir = fallback
        log_dir = fallback / "logs"

    dirs = [
        data_dir,
        data_dir / "attachments",
        data_dir / "backups",
        log_dir,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug("Directorio verificado: %s", d)
