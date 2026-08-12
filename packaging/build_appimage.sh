#!/bin/bash
# Script para crear AppImage de JL Mantenimiento
# Requiere: linuxdeploy, python3, PyQt6 instaladas localmente

set -e

APPDIR="AppDir"
APP_NAME="jl-mantenimiento"
VERSION="0.1.0"

echo "Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

# Copy desktop file
cp packaging/jl-mantenimiento.desktop "$APPDIR/usr/share/applications/"

# Copy appdata
cp packaging/jl-mantenimiento.appdata.xml "$APPDIR/usr/share/metainfo/"

# Copy source
cp -r src "$APPDIR/usr/lib/luciotech"

# Create entry point
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec python3 -m luciotech.main "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo "AppDir created in $APPDIR/"
echo "To build AppImage, run: linuxdeploy --appdir=$APPDIR --output=appimage"
