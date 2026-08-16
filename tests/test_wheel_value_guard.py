"""Pruebas del bloqueo global de cambios de valor mediante desplazamiento."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QCoreApplication, QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QScrollArea,
    QWidget,
)

from luciotech.app import _SafeQApplication


def _app() -> _SafeQApplication:
    instance = QCoreApplication.instance()
    if instance is None:
        return _SafeQApplication([])
    assert isinstance(instance, _SafeQApplication)
    return instance


def _wheel_event(*, touchpad: bool = False) -> QWheelEvent:
    return QWheelEvent(
        QPointF(5, 5),
        QPointF(5, 5),
        QPoint(0, -30) if touchpad else QPoint(),
        QPoint() if touchpad else QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate if touchpad else Qt.ScrollPhase.NoScrollPhase,
        False,
        (
            Qt.MouseEventSource.MouseEventSynthesizedBySystem
            if touchpad
            else Qt.MouseEventSource.MouseEventNotSynthesized
        ),
    )


def test_mouse_wheel_does_not_change_editable_values() -> None:
    app = _app()
    controls = [QDoubleSpinBox(), QDateEdit(), QComboBox()]
    controls[0].setValue(10)
    controls[1].setDate(controls[1].date().addDays(10))
    controls[2].addItems(["Normal", "Alta", "Urgente"])
    controls[2].setCurrentIndex(1)
    original_values = [
        controls[0].value(),
        controls[1].date(),
        controls[2].currentIndex(),
    ]

    for control in controls:
        QCoreApplication.sendEvent(control, _wheel_event())
        app.processEvents()

    assert controls[0].value() == original_values[0]
    assert controls[1].date() == original_values[1]
    assert controls[2].currentIndex() == original_values[2]


def test_touchpad_scroll_does_not_change_spinbox_value() -> None:
    app = _app()
    spin = QDoubleSpinBox()
    spin.setValue(25)

    QCoreApplication.sendEvent(spin, _wheel_event(touchpad=True))
    app.processEvents()

    assert spin.value() == 25


@pytest.mark.parametrize("touchpad", [False, True])
def test_scroll_over_value_control_moves_containing_page(touchpad: bool) -> None:
    app = _app()
    scroll = QScrollArea()
    scroll.resize(240, 180)
    content = QWidget()
    content.setFixedSize(220, 900)
    spin = QDoubleSpinBox(content)
    spin.move(20, 80)
    spin.setValue(15)
    scroll.setWidget(content)
    assert scroll.verticalScrollBar().maximum() > 0

    QCoreApplication.sendEvent(spin, _wheel_event(touchpad=touchpad))
    app.processEvents()

    assert spin.value() == 15
    assert scroll.verticalScrollBar().value() > 0
