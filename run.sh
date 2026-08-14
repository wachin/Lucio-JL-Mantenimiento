#!/bin/bash
# Ejecutar JL Mantenimiento
# NOTE: Do NOT run with '&' (background) — Qt needs the terminal for the event loop.
cd "$(dirname "$0")"
export QT_LOGGING_RULES="*.debug=false;qt6ct.*=false"
export PYTHONPATH=src
exec python3 -m luciotech.main
