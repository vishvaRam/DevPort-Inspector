#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If the script is placed inside a subfolder (e.g. scripts/), use parent; otherwise use current directory
if [ -f "${SCRIPT_DIR}/app.py" ]; then
    PROJECT_ROOT="${SCRIPT_DIR}"
else
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
fi
cd "$PROJECT_ROOT"

APP_NAME="devport-inspector"
VERSION="1.0.0"
ARCH="amd64"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}.deb"

RELEASE_DIR="${PROJECT_ROOT}/releases"
BUILD_DIR="${PROJECT_ROOT}/build"
STAGE_ROOT=$(mktemp -d /tmp/deb-build-XXXXXX)
PKG_DIR="${STAGE_ROOT}/${APP_NAME}_${VERSION}_${ARCH}"

echo "==> Project root: ${PROJECT_ROOT}"
echo "==> Cleaning old build artifacts..."
rm -rf build dist "${RELEASE_DIR}/${DEB_NAME}"
mkdir -p "${RELEASE_DIR}" "${BUILD_DIR}"

# 1. Build PyInstaller bundle
echo "==> Freezing application with PyInstaller..."
uv run pyinstaller --noconfirm --onedir --windowed \
    --name "${APP_NAME}" \
    --specpath "${BUILD_DIR}" \
    --hidden-import "psutil" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtWidgets" \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    app.py

# 2. Setup standard Linux packaging filesystem
echo "==> Assembling deb package structure..."
mkdir -p "${PKG_DIR}/opt/${APP_NAME}"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/DEBIAN"

# Copy binary & runtime assets
cp -a "dist/${APP_NAME}/." "${PKG_DIR}/opt/${APP_NAME}/"
ln -s "/opt/${APP_NAME}/${APP_NAME}" "${PKG_DIR}/usr/bin/${APP_NAME}"

# Install desktop icon (using the generated 512/256 PNG)
if [ -f "${PROJECT_ROOT}/assets/icon.png" ]; then
    cp "${PROJECT_ROOT}/assets/icon.png" "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

# 3. Generate Desktop Entry
cat << EOF > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop"
[Desktop Entry]
Name=DevPort Inspector
Comment=Local Dev Port Inspector and Zombie Process Manager
Exec=/usr/bin/${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Development;System;Utility;
StartupWMClass=devport-inspector
EOF

# 4. Generate Control File
cat << EOF > "${PKG_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Section: devel
Priority: optional
Architecture: ${ARCH}
Depends: libxcb-cursor0, libgl1, libxcb1
Maintainer: Vishva Ramamurthy
Description: DevPort Inspector & Zombie Process Killer
 Modern PyQt6 dashboard for monitoring active listening TCP ports,
 managing stuck daemons, and executing graceful SIGTERM/SIGKILL cycles.
EOF

# 5. Fix permissions & Build Package
chmod -R 755 "${PKG_DIR}"
chmod 644 "${PKG_DIR}/DEBIAN/control"
chmod 644 "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop"
if [ -f "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png" ]; then
    chmod 644 "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

echo "==> Building .deb package..."
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${RELEASE_DIR}/${DEB_NAME}"
rm -rf "${STAGE_ROOT}"

echo "✅ Linux package generated at: ${RELEASE_DIR}/${DEB_NAME}"