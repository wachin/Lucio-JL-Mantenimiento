"""Punto de entrada de la aplicación."""

from __future__ import annotations

import sys

from luciotech.app import create_application


def main() -> None:
    """Iniciar la aplicación JL Mantenimiento."""
    app = create_application(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
