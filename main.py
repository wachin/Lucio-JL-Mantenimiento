"""Lanzador directo de JL Mantenimiento desde la raíz del proyecto."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Evitar problemas conocidos de qt6ct al iniciar directamente en Linux.
# setdefault permite seleccionar otro backend, por ejemplo ``wayland``.
if sys.platform.startswith("linux"):
    os.environ["QT_QPA_PLATFORMTHEME"] = ""
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt6ct.*=false")

from luciotech.main import main


if __name__ == "__main__":
    main()
