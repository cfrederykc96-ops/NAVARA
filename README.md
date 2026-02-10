# POS Tienda de Ropa - Primera versión instalable

MVP instalable en local con Python (sin dependencias externas), incluye:
- Inventario por prenda (SKU, código de barras, talla, color, corte, precio, stock)
- Gestión de clientes
- Registro de ventas
- Factura/tirilla imprimible
- Descuento automático de inventario al vender

## Requisitos
- Python 3.10+

## Instalación y ejecución
```bash
python pos_server.py
```

Abrir en navegador:
- `http://localhost:8000`

## Cómo usar
1. En **Inventario**, registra tus productos.
2. En **Clientes**, registra clientes (opcional para venta).
3. En **Nueva venta**, agrega líneas de productos y cantidades, selecciona método de pago y cobra.
4. El sistema genera la **factura** y puedes usar **Imprimir tirilla**.

## Base de datos
- SQLite local: `pos.db` (se crea automáticamente).

## Notas
- Tasa de impuesto configurable en `TAX_RATE` dentro de `pos_server.py`.
