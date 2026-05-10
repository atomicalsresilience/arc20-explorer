#!/bin/bash
# Build script for ARC-20 Explorer v1.0.0
# Bitwork Labs

set -e

VERSION="1.0.0"
APP_NAME="arc20-explorer"
DIST_NAME="${APP_NAME}-v${VERSION}-linux-x86_64"

echo "════════════════════════════════════════════════"
echo "  ARC-20 EXPLORER · BUILD v${VERSION}"
echo "════════════════════════════════════════════════"

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "✗ venv no encontrado, créalo primero"
    exit 1
fi
source venv/bin/activate

echo ""
echo "── Instalando dependencias..."
pip install -q -r requirements.txt

echo ""
echo "── Limpiando build/ y dist/..."
rm -rf build/ dist/ __pycache__/

echo ""
echo "── Ejecutando PyInstaller..."
pyinstaller --clean --noconfirm arc20_explorer.spec

if [ ! -f "dist/${APP_NAME}" ]; then
    echo "✗ Error: dist/${APP_NAME} no creado"
    exit 1
fi

SIZE=$(du -h "dist/${APP_NAME}" | cut -f1)
echo ""
echo "✓ Binario creado: dist/${APP_NAME} (${SIZE})"

echo ""
echo "── Empaquetando ${DIST_NAME}.tar.gz..."

PKG_DIR="dist/${DIST_NAME}"
mkdir -p "$PKG_DIR"
cp "dist/${APP_NAME}" "$PKG_DIR/"
cp README.md "$PKG_DIR/"
cp LICENSE "$PKG_DIR/"
cp -r i18n "$PKG_DIR/i18n_source"

cd dist
tar czf "${DIST_NAME}.tar.gz" "${DIST_NAME}/"
cd ..

PKG_SIZE=$(du -h "dist/${DIST_NAME}.tar.gz" | cut -f1)
echo ""
echo "✓ Paquete: dist/${DIST_NAME}.tar.gz (${PKG_SIZE})"

echo ""
echo "── Generando checksums..."
./checksums.sh

echo ""
echo "════════════════════════════════════════════════"
echo "  BUILD COMPLETADO"
echo "════════════════════════════════════════════════"
ls -lh dist/*.tar.gz dist/*.txt 2>/dev/null

echo ""
echo "Próximos pasos:"
echo "  1. Probar: ./dist/${APP_NAME}"
echo "  2. Crear release en GitHub con dist/${DIST_NAME}.tar.gz"
echo "  3. Adjuntar dist/checksums.txt al release"
