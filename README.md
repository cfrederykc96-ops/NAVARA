# POS Tienda de Ropa — TODO EN UNO (instalable local)

Este proyecto ya viene listo como **“todo en uno”** para que lo puedas usar sin configurar frameworks.

Incluye:
- Inventario por prenda (SKU, código de barras, talla, color, corte, precio, stock).
- Clientes.
- Ventas (con descuento automático de inventario).
- Factura/tirilla imprimible.
- Base de datos local SQLite (`pos.db`).

---

## 1) Requisitos mínimos
- Linux/macOS/WSL con terminal.
- Python 3.10 o superior.
- Navegador web (Chrome/Firefox/Edge).

Verifica Python:
```bash
python3 --version
```

---

## 2) Instalación TODO EN UNO (recomendada)
Desde la carpeta del proyecto ejecuta:
```bash
./instalar_pos.sh
```

Este instalador:
1. Verifica Python.
2. Inicializa la base de datos (`pos.db`).
3. Genera script de arranque rápido (`iniciar_pos.sh`).
4. Intenta crear acceso directo en el escritorio (Linux) llamado **POS-Tienda-Ropa**.

---

## 3) Cómo iniciar la aplicación
```bash
./iniciar_pos.sh
```

Cuando veas el mensaje de servidor activo, abre:
- `http://localhost:8000`

> Para detener la app: en la terminal, presiona `Ctrl + C`.

---

## 4) Cómo usar el POS (paso a paso)
1. **Inventario**
   - Crea productos con nombre, SKU, barcode, talla, color, corte, precio y stock.
2. **Clientes**
   - Registra clientes (opcional, también puedes vender como consumidor final).
3. **Nueva venta**
   - Selecciona cliente, método de pago, agrega líneas de productos y cantidades.
   - Pulsa **Cobrar y generar factura**.
4. **Factura / Tirilla**
   - Se abre la factura automáticamente.
   - Pulsa **Imprimir tirilla** para imprimir comprobante.

---

## 5) ¿Cómo “convertirlo en aplicación” de verdad?
Tienes dos niveles:

### Nivel A — App local de escritorio (rápido)
Ya lo tienes: ejecutas `./iniciar_pos.sh` y lo abres en navegador.
Con `./instalar_pos.sh` se crea un acceso directo (si tu sistema lo permite).

### Nivel B — App para negocio en producción
Recomendado para operar en tienda real:
1. Poner este POS en un mini-PC de caja.
2. Activar copias de seguridad automáticas de `pos.db`.
3. Configurar impresora térmica real.
4. Agregar usuarios/roles, cierre de caja, reportes y multi-sucursal.
5. Migrar luego a backend web robusto (API + frontend + nube).

---

## 6) Respaldo y recuperación (IMPORTANTE)
Tu información está en `pos.db`.

### Hacer backup manual
```bash
cp pos.db backup-pos-$(date +%F-%H%M).db
```

### Restaurar backup
```bash
cp backup-pos-AAAA-MM-DD-HHMM.db pos.db
```

---

## 7) Solución de problemas

### “No abre localhost:8000”
- Verifica que la terminal siga corriendo `./iniciar_pos.sh`.
- Revisa si el puerto 8000 está ocupado por otra app.

### “No tengo permisos para ejecutar scripts”
```bash
chmod +x instalar_pos.sh iniciar_pos.sh
```

### “No existe python3”
Instala Python 3 y vuelve a correr:
```bash
./instalar_pos.sh
```

---

## 8) Arranque rápido (resumen corto)
```bash
chmod +x instalar_pos.sh iniciar_pos.sh
./instalar_pos.sh
./iniciar_pos.sh
```
Abrir: `http://localhost:8000`

---

## 9) Archivos principales
- `pos_server.py` → servidor + lógica POS + SQLite.
- `instalar_pos.sh` → instalación automática todo en uno.
- `iniciar_pos.sh` → arranque rápido.
- `pos.db` → base de datos local (se crea automática).
