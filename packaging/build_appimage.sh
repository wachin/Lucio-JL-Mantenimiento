#!/bin/bash
# Script para crear AppImage de JL Mantenimiento
# Requiere: linuxdeploy (o appimagetool), python3, PyQt6
#
# Uso:
#   ./packaging/build_appimage.sh
#
# Para construir el AppImage final necesitas linuxdeploy o appimagetool:
#   linuxdeploy --appdir=packaging/AppDir --output=appimage
#   # o
#   appimagetool packaging/AppDir

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APPDIR="$SCRIPT_DIR/AppDir"
APP_NAME="jl-mantenimiento"
VERSION="0.2.0"

echo "=== JL Mantenimiento AppImage Builder ==="
echo "Project: $PROJECT_DIR"
echo "AppDir:  $APPDIR"
echo "Version: $VERSION"

# Limpiar AppDir anterior
rm -rf "$APPDIR"

echo ""
echo "--- Creando estructura AppDir ---"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/python3/dist-packages"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

echo "--- Copiando código fuente ---"
cp -r "$PROJECT_DIR/src/luciotech" "$APPDIR/usr/lib/python3/dist-packages/"

echo "--- Copiando archivos de empaquetado ---"
cp "$SCRIPT_DIR/jl-mantenimiento.desktop" "$APPDIR/usr/share/applications/"
cp "$SCRIPT_DIR/jl-mantenimiento.appdata.xml" "$APPDIR/usr/share/metainfo/"

echo "--- Creando punto de entrada ---"
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$HERE/usr/lib/python3/dist-packages:${PYTHONPATH}"
export PATH="$HERE/usr/bin:${PATH}"
exec python3 -c "from luciotech.main import main; main()" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "--- Creando archivo .desktop ---"
cat > "$APPDIR/jl-mantenimiento.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=JL Mantenimiento
Comment=Sistema de recepción y reparación de equipos
Exec=jl-mantenimiento
Icon=jl-mantenimiento
Categories=Office;
DESKTOP

echo ""
echo "=== AppDir creado en $APPDIR ==="
echo ""
echo "Para generar el AppImage necesitas linuxdeploy o appimagetool:"
echo "  linuxdeploy --appdir=$APPDIR --output=appimage"
echo "  # o"
echo "  appimagetool $APPDIR"
echo ""
echo "Nota: Asegúrate de tener PyQt6 y las dependencias instaladas"
echo "dentro del AppDir o en el sistema donde se ejecute."
