#!/usr/bin/env bash

# Ejecutar JL Mantenimiento desde el repositorio o mediante un enlace simbólico.
set -eu

launcher_path="$(readlink -f -- "${BASH_SOURCE[0]}")"
project_dir="$(dirname -- "$launcher_path")"
cd "$project_dir"

export QT_QPA_PLATFORMTHEME=
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
export QT_LOGGING_RULES='*.debug=false;qt6ct.*=false'

exec "${LUCIO_PYTHON:-python3}" main.py "$@"
