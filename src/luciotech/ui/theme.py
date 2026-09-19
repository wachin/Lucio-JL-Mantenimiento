"""Temas visuales compartidos por el arranque, Configuración y la barra de herramientas.

Modos disponibles (se persisten textualmente en Configuración):

- ``Oscuro``: paleta Fusion oscura fija.
- ``Claro``: paleta Fusion clara fija.
- ``Sistema``: sigue el modo claro/oscuro del sistema y **vuelve a aplicarse
  en vivo** si el sistema cambia con la aplicación abierta.
"""

from __future__ import annotations

import logging
import sys

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modos de tema seleccionables
# ---------------------------------------------------------------------------

THEME_DARK = "Oscuro"
THEME_LIGHT = "Claro"
THEME_SYSTEM = "Sistema"

DEFAULT_THEME = THEME_SYSTEM

THEMES: dict[str, str] = {
    THEME_SYSTEM: "auto",
    THEME_LIGHT: "fusion_light",
    THEME_DARK: "fusion_dark",
}

# Nombres usados por versiones anteriores de la configuración. Describían lo
# que se veía al arrancar (no la elección del usuario) y solo se resolvían al
# iniciar, por eso al cambiar el tema de Windows el programa no acompañaba.
# Se traducen al modo moderno equivalente al cargar la configuración.
_THEME_ALIASES: dict[str, str] = {
    "Claro (sistema)": THEME_SYSTEM,
    "Oscuro (Fusion)": THEME_DARK,
    "Claro (Fusion)": THEME_LIGHT,
}


def normalize_theme_name(value: str | None) -> str:
    """Traducir cualquier nombre de tema conocido a un modo actual.

    Los nombres antiguos y los desconocidos vuelven a :data:`DEFAULT_THEME`.
    """
    if not value:
        return DEFAULT_THEME
    if value in THEMES:
        return value
    return _THEME_ALIASES.get(value, DEFAULT_THEME)


# ---------------------------------------------------------------------------
# Detección de la preferencia claro/oscuro del sistema
# ---------------------------------------------------------------------------

def _windows_prefers_dark_mode() -> bool | None:
    """Leer la preferencia claro/oscuro del sistema (solo Windows).

    Devuelve ``None`` cuando no se puede determinar (otra plataforma,
    registro no disponible), para que el llamador use otra fuente.
    """
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


def system_prefers_dark(
    scheme: Qt.ColorScheme | None = None, app: QApplication | None = None
) -> bool:
    """Preferencia claro/oscuro del sistema: registro de Windows y, si no, Qt."""
    preference = _windows_prefers_dark_mode()
    if preference is not None:
        return preference

    if scheme is None and app is not None:
        try:
            scheme = app.styleHints().colorScheme()
        except (AttributeError, RuntimeError):  # pragma: no cover - Qt antiguo
            scheme = None
    if scheme is not None and scheme != Qt.ColorScheme.Unknown:
        return scheme == Qt.ColorScheme.Dark
    return False


# ---------------------------------------------------------------------------
# Paletas
# ---------------------------------------------------------------------------

def _apply_fusion_dark(app: QApplication) -> None:
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


def _apply_fusion_light(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())


# ---------------------------------------------------------------------------
# Gestor de tema con seguimiento en vivo del sistema
# ---------------------------------------------------------------------------

class ThemeManager(QObject):
    """Aplica el tema elegido y sigue en vivo el modo del sistema.

    El modo ``Sistema`` no se resuelve una sola vez al arrancar: se conecta a
    ``QStyleHints.colorSchemeChanged`` para reaplicar la paleta cuando el
    sistema cambia entre claro y oscuro con la aplicación abierta.
    """

    #: Emite el modo en vigor ("Claro" u "Oscuro") tras cada aplicación.
    theme_changed = pyqtSignal(str)

    _instance: "ThemeManager | None" = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        super().__init__()
        self._app: QApplication | None = None
        self._mode: str = DEFAULT_THEME
        self._scheme_connected = False
        self._last_scheme: Qt.ColorScheme | None = None

    @property
    def mode(self) -> str:
        """Modo elegido por el usuario (puede ser "Sistema")."""
        return self._mode

    def effective_mode(self, scheme: Qt.ColorScheme | None = None) -> str:
        """Modo realmente aplicado ("Claro" u "Oscuro")."""
        if self._mode != THEME_SYSTEM:
            return self._mode
        if scheme is None:
            scheme = self._last_scheme
        return (
            THEME_DARK
            if system_prefers_dark(scheme, self._app)
            else THEME_LIGHT
        )

    def apply(self, app: QApplication, mode: str) -> None:
        """Aplicar *mode* a *app* y activar el seguimiento del sistema."""
        self._app = app
        self._mode = normalize_theme_name(mode)
        self._last_scheme = None
        self._connect_scheme_watch(app)
        self._apply_now()

    def refresh_system_scheme(self, scheme: Qt.ColorScheme | None = None) -> None:
        """Reaplicar el tema; útil cuando el sistema cambia de claro/oscuro."""
        if scheme is not None:
            self._last_scheme = scheme
        if self._mode == THEME_SYSTEM:
            self._apply_now(scheme if scheme is not None else self._last_scheme)

    def _connect_scheme_watch(self, app: QApplication) -> None:
        if self._scheme_connected:
            return
        try:
            app.styleHints().colorSchemeChanged.connect(self._on_scheme_changed)
            self._scheme_connected = True
        except (AttributeError, RuntimeError):  # pragma: no cover - Qt antiguo
            logger.warning(
                "Este sistema no informa cambios de tema en vivo", exc_info=True
            )

    def _on_scheme_changed(self, scheme: Qt.ColorScheme) -> None:
        self.refresh_system_scheme(scheme)

    def _apply_now(self, scheme: Qt.ColorScheme | None = None) -> None:
        app = self._app
        if app is None:
            return
        effective = self.effective_mode(scheme)
        if effective == THEME_DARK:
            _apply_fusion_dark(app)
        else:
            _apply_fusion_light(app)
        self.theme_changed.emit(effective)


def apply_theme(app: QApplication | None, theme_name: str) -> None:
    """Aplicar un modo de tema y activar el seguimiento del sistema."""
    if app is None:
        return
    ThemeManager.instance().apply(app, theme_name)
