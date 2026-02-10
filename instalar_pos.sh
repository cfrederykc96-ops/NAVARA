#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ No se encontró python3. Instálalo y vuelve a intentar."
  exit 1
fi

PY_VERSION="$(python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

echo "✅ Python detectado: $PY_VERSION"
echo "✅ Este POS no requiere instalar librerías externas."

echo "🗄️ Inicializando base de datos local (pos.db)..."
python3 - <<'PY'
import pos_server
pos_server.init_db()
print("OK")
PY

echo "🧩 Creando script de inicio rápido..."
cat > iniciar_pos.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
python3 pos_server.py
SH
chmod +x iniciar_pos.sh

if [ -d "$HOME/Desktop" ]; then
  DESKTOP_FILE="$HOME/Desktop/POS-Tienda-Ropa.desktop"
  cat > "$DESKTOP_FILE" <<DESK
[Desktop Entry]
Type=Application
Name=POS Tienda Ropa
Comment=Abrir POS local de tienda de ropa
Exec=bash -lc 'cd "$PROJECT_DIR" && ./iniciar_pos.sh'
Terminal=true
Categories=Office;
DESK
  chmod +x "$DESKTOP_FILE" || true
  echo "✅ Acceso directo creado en Escritorio: $DESKTOP_FILE"
else
  echo "⚠️ No se encontró carpeta Desktop. Se omite acceso directo."
fi

echo "\n🎉 Instalación lista. Para iniciar:"
echo "   cd $PROJECT_DIR"
echo "   ./iniciar_pos.sh"
echo "\nLuego abre en tu navegador: http://localhost:8000"
