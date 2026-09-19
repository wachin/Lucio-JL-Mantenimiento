"""Cambio de tema: modos Oscuro/Claro/Sistema, seguimiento del sistema y persistencia."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from luciotech.ui.theme import (
    DEFAULT_THEME,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    ThemeManager,
    normalize_theme_name,
    system_prefers_dark,
)

_app_holder: list[object] = []


def _app():
    """QApplication compartida conservando referencia (ver AGENTS.md)."""
    from PyQt6.QtCore import QCoreApplication
    from luciotech.app import _SafeQApplication

    instance = QCoreApplication.instance()
    if instance is None:
        app = _SafeQApplication([])
        _app_holder.append(app)
        return app
    return instance


# ---------------------------------------------------------------------------
# Nombres de tema
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (THEME_SYSTEM, THEME_SYSTEM),
        (THEME_LIGHT, THEME_LIGHT),
        (THEME_DARK, THEME_DARK),
        # Nombres de versiones anteriores de la configuración
        ("Claro (sistema)", THEME_SYSTEM),
        ("Oscuro (Fusion)", THEME_DARK),
        ("Claro (Fusion)", THEME_LIGHT),
        ("", DEFAULT_THEME),
        (None, DEFAULT_THEME),
        ("Temario inventado", DEFAULT_THEME),
    ],
)
def test_normalize_theme_name(raw: str | None, expected: str) -> None:
    assert normalize_theme_name(raw) == expected


# ---------------------------------------------------------------------------
# Paletas aplicadas
# ---------------------------------------------------------------------------

def _palette_is_dark(app) -> bool:
    color = app.palette().color(app.palette().ColorRole.Window)
    return color.lightness() < 128


def test_apply_dark_and_light_changes_palette() -> None:
    app = _app()
    manager = ThemeManager.instance()
    manager._scheme_connected = False

    manager.apply(app, THEME_DARK)
    assert manager.mode == THEME_DARK
    assert manager.effective_mode() == THEME_DARK
    assert _palette_is_dark(app)

    manager.apply(app, THEME_LIGHT)
    assert manager.mode == THEME_LIGHT
    assert manager.effective_mode() == THEME_LIGHT
    assert not _palette_is_dark(app)


# ---------------------------------------------------------------------------
# Modo Sistema
# ---------------------------------------------------------------------------

def _reset_manager_watch() -> None:
    manager = ThemeManager.instance()
    manager._scheme_connected = False


def test_system_mode_uses_windows_registry_preference() -> None:
    app = _app()
    _reset_manager_watch()
    manager = ThemeManager.instance()

    with patch("luciotech.ui.theme._windows_prefers_dark_mode", return_value=True):
        manager.apply(app, THEME_SYSTEM)
        assert manager.mode == THEME_SYSTEM
        assert manager.effective_mode() == THEME_DARK
        assert _palette_is_dark(app)

    with patch("luciotech.ui.theme._windows_prefers_dark_mode", return_value=False):
        manager.apply(app, THEME_SYSTEM)
        assert manager.effective_mode() == THEME_LIGHT
        assert not _palette_is_dark(app)


def test_system_mode_follows_scheme_change_in_live() -> None:
    """Con modo Sistema, un cambio del sistema reaplica la paleta en vivo."""
    from PyQt6.QtCore import Qt

    app = _app()
    _reset_manager_watch()
    manager = ThemeManager.instance()
    signals: list[str] = []
    manager.theme_changed.connect(signals.append)

    with patch("luciotech.ui.theme._windows_prefers_dark_mode", return_value=None):
        manager.apply(app, THEME_SYSTEM)
        assert manager.effective_mode() == THEME_LIGHT  # sin preferencia conocida

        manager.refresh_system_scheme(Qt.ColorScheme.Dark)
        assert manager.effective_mode() == THEME_DARK
        assert _palette_is_dark(app)

        manager.refresh_system_scheme(Qt.ColorScheme.Light)
        assert manager.effective_mode() == THEME_LIGHT
        assert not _palette_is_dark(app)

    # Cada reaplicación en vivo avisa a los interesados (botón de la toolbar)
    assert signals[-2:] == [THEME_DARK, THEME_LIGHT]


def test_fixed_mode_ignores_scheme_changes() -> None:
    """Con tema fijo, los cambios del sistema no alteran la paleta."""
    from PyQt6.QtCore import Qt

    app = _app()
    _reset_manager_watch()
    manager = ThemeManager.instance()
    manager.apply(app, THEME_LIGHT)

    manager.refresh_system_scheme(Qt.ColorScheme.Dark)
    assert manager.mode == THEME_LIGHT
    assert not _palette_is_dark(app)


def test_system_prefers_dark_falls_back_to_scheme() -> None:
    """Sin registro de Windows (otra plataforma), usa el esquema de Qt."""
    from PyQt6.QtCore import Qt

    with patch("luciotech.ui.theme._windows_prefers_dark_mode", return_value=None):
        assert system_prefers_dark(Qt.ColorScheme.Dark) is True
        assert system_prefers_dark(Qt.ColorScheme.Light) is False
        assert system_prefers_dark(None) is False  # desconocido -> claro


# ---------------------------------------------------------------------------
# Persistencia y UI
# ---------------------------------------------------------------------------

@pytest.fixture()
def isolated_settings(tmp_path: Path):
    """Base de datos aislada para SettingsService."""
    db_path = tmp_path / "database.sqlite3"
    patches = [
        patch("luciotech.config.get_data_dir", return_value=tmp_path),
        patch("luciotech.config.get_log_dir", return_value=tmp_path / "logs"),
        patch("luciotech.config.get_db_path", return_value=db_path),
        patch("luciotech.database.connection.get_db_path", return_value=db_path),
        # main_window importa get_data_dir directamente (estado de ventana)
        patch("luciotech.ui.main_window.get_data_dir", return_value=tmp_path),
    ]
    for item in patches:
        item.start()
    from luciotech.database.connection import init_db, reset_connection

    reset_connection()
    init_db()
    try:
        yield tmp_path
    finally:
        reset_connection()
        for item in patches:
            item.stop()


def test_theme_persisted_and_reloaded(isolated_settings: Path) -> None:
    from luciotech.services.settings_service import SettingsService

    service = SettingsService()
    service.set("theme", THEME_DARK)

    reloaded = SettingsService()
    assert reloaded.get("theme", DEFAULT_THEME) == THEME_DARK


def test_settings_dialog_normalizes_legacy_name(isolated_settings: Path) -> None:
    """Un valor antiguo guardado se muestra con el nombre nuevo del modo."""
    from luciotech.services.settings_service import SettingsService
    from luciotech.ui.dialogs.settings_dialog import SettingsDialog

    SettingsService().set("theme", "Claro (sistema)")
    _app()
    dialog = SettingsDialog()
    try:
        assert dialog._theme_combo.currentText() == THEME_SYSTEM
    finally:
        dialog.deleteLater()


def test_toolbar_theme_button_toggles_and_persists(
    isolated_settings: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El botón rápido alterna el tema y guarda la elección."""
    from luciotech.services.settings_service import SettingsService
    from luciotech.ui.main_window import MainWindow
    from luciotech.ui.theme import ThemeManager

    # Tema inicial conocido y aplicado, para no depender del registro de Windows
    SettingsService().set("theme", THEME_LIGHT)
    app = _app()
    ThemeManager.instance().apply(app, THEME_LIGHT)
    window = MainWindow()
    try:
        assert window._theme_action.text() == f"Tema: {THEME_LIGHT}"

        window._toggle_theme()
        assert window._theme_action.text() == f"Tema: {THEME_DARK}"
        assert SettingsService().get("theme") == THEME_DARK

        window._toggle_theme()
        assert window._theme_action.text() == f"Tema: {THEME_LIGHT}"
        assert SettingsService().get("theme") == THEME_LIGHT

        # El botón siempre refleja el gestor (p. ej. tras cambio del sistema)
        ThemeManager.instance().theme_changed.emit(THEME_DARK)
        assert window._theme_action.text() == f"Tema: {THEME_DARK}"
    finally:
        window.close()
