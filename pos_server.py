import html
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "pos.db"
HOST = "0.0.0.0"
PORT = 8000
TAX_RATE = 0.19


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            barcode TEXT NOT NULL UNIQUE,
            size TEXT,
            color TEXT,
            cut TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            document TEXT,
            phone TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            client_id INTEGER,
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def layout(title: str, body: str):
    return f"""<!doctype html>
<html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{title}</title>
<style>
body{{font-family:Arial;margin:0;background:#f6f7fb}}header{{background:#1f2a44;color:#fff;padding:16px}}
nav a{{color:#fff;margin-right:12px;text-decoration:none}}main{{padding:20px}}table{{width:100%;border-collapse:collapse;background:#fff}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}input,select,button{{padding:8px;margin:4px 0}}button{{background:#1f5ef0;color:#fff;border:0;border-radius:6px}}
.card{{display:inline-block;background:#fff;padding:12px;margin-right:8px;border-radius:8px}}.line{{display:flex;gap:8px;margin-bottom:8px}}
</style></head><body>
<header><h1>POS Tienda Ropa</h1><nav>
<a href='/'>Inicio</a><a href='/products'>Inventario</a><a href='/clients'>Clientes</a><a href='/sales/new'>Nueva venta</a>
</nav></header><main>{body}</main></body></html>"""


class POSHandler(BaseHTTPRequestHandler):
    def _send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _parse_post(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return parse_qs(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.show_home()
        if path == "/products":
            return self.show_products()
        if path == "/clients":
            return self.show_clients()
        if path == "/sales/new":
            return self.show_new_sale()
        if path.startswith("/invoices/"):
            try:
                sale_id = int(path.split("/")[-1])
            except ValueError:
                return self._send_html(layout("Error", "ID inválido"), 400)
            return self.show_invoice(sale_id)
        return self._send_html(layout("404", "No encontrado"), 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/products":
            return self.create_product()
        if path == "/clients":
            return self.create_client()
        if path == "/sales/new":
            return self.create_sale()
        return self._send_html(layout("404", "No encontrado"), 404)

    def show_home(self):
        conn = db_conn()
        total_products = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        total_clients = conn.execute("SELECT COUNT(*) c FROM clients").fetchone()["c"]
        low = conn.execute("SELECT name, sku, stock FROM products WHERE stock <= 3 ORDER BY stock").fetchall()
        sales = conn.execute("SELECT id, created_at, total FROM sales ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()

        low_rows = "".join([f"<tr><td>{html.escape(r['name'])}</td><td>{html.escape(r['sku'])}</td><td>{r['stock']}</td></tr>" for r in low]) or "<tr><td colspan='3'>Sin alertas</td></tr>"
        sale_rows = "".join([f"<tr><td>{r['id']}</td><td>{r['created_at']}</td><td>${r['total']:.2f}</td><td><a href='/invoices/{r['id']}'>Ver</a></td></tr>" for r in sales]) or "<tr><td colspan='4'>Sin ventas</td></tr>"

        body = f"""
<div class='card'><b>Productos:</b> {total_products}</div>
<div class='card'><b>Clientes:</b> {total_clients}</div>
<h2>Stock bajo</h2><table><tr><th>Producto</th><th>SKU</th><th>Stock</th></tr>{low_rows}</table>
<h2>Ventas recientes</h2><table><tr><th>ID</th><th>Fecha</th><th>Total</th><th>Factura</th></tr>{sale_rows}</table>
"""
        self._send_html(layout("Inicio", body))

    def show_products(self):
        conn = db_conn()
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        conn.close()
        tr = "".join([
            f"<tr><td>{r['id']}</td><td>{html.escape(r['name'])}</td><td>{html.escape(r['sku'])}</td><td>{html.escape(r['barcode'])}</td><td>{html.escape(r['size'] or '')}</td><td>{html.escape(r['color'] or '')}</td><td>{html.escape(r['cut'] or '')}</td><td>${r['price']:.2f}</td><td>{r['stock']}</td></tr>"
            for r in rows
        ]) or "<tr><td colspan='9'>Sin productos</td></tr>"
        body = f"""
<h2>Inventario</h2>
<form method='post' action='/products'>
<input name='name' placeholder='Nombre' required>
<input name='sku' placeholder='SKU' required>
<input name='barcode' placeholder='Código de barras' required>
<input name='size' placeholder='Talla'>
<input name='color' placeholder='Color'>
<input name='cut' placeholder='Corte/Fit'>
<input name='price' placeholder='Precio' type='number' step='0.01' required>
<input name='stock' placeholder='Stock' type='number' required>
<button type='submit'>Guardar producto</button>
</form>
<table><tr><th>ID</th><th>Nombre</th><th>SKU</th><th>Barcode</th><th>Talla</th><th>Color</th><th>Corte</th><th>Precio</th><th>Stock</th></tr>{tr}</table>
"""
        self._send_html(layout("Inventario", body))

    def create_product(self):
        p = self._parse_post()
        conn = db_conn()
        try:
            conn.execute(
                "INSERT INTO products(name, sku, barcode, size, color, cut, price, stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    p.get("name", [""])[0], p.get("sku", [""])[0], p.get("barcode", [""])[0], p.get("size", [""])[0],
                    p.get("color", [""])[0], p.get("cut", [""])[0], float(p.get("price", ["0"])[0]), int(p.get("stock", ["0"])[0])
                ),
            )
            conn.commit()
        finally:
            conn.close()
        self._redirect("/products")

    def show_clients(self):
        conn = db_conn()
        rows = conn.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
        conn.close()
        tr = "".join([f"<tr><td>{r['id']}</td><td>{html.escape(r['name'])}</td><td>{html.escape(r['document'] or '')}</td><td>{html.escape(r['phone'] or '')}</td><td>{html.escape(r['email'] or '')}</td></tr>" for r in rows]) or "<tr><td colspan='5'>Sin clientes</td></tr>"
        body = f"""
<h2>Clientes</h2>
<form method='post' action='/clients'>
<input name='name' placeholder='Nombre' required>
<input name='document' placeholder='Documento'>
<input name='phone' placeholder='Teléfono'>
<input name='email' placeholder='Email'>
<button type='submit'>Guardar cliente</button>
</form>
<table><tr><th>ID</th><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th></tr>{tr}</table>
"""
        self._send_html(layout("Clientes", body))

    def create_client(self):
        p = self._parse_post()
        conn = db_conn()
        conn.execute(
            "INSERT INTO clients(name, document, phone, email) VALUES (?, ?, ?, ?)",
            (p.get("name", [""])[0], p.get("document", [""])[0], p.get("phone", [""])[0], p.get("email", [""])[0]),
        )
        conn.commit()
        conn.close()
        self._redirect("/clients")

    def show_new_sale(self):
        conn = db_conn()
        products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        conn.close()

        product_options = "".join([f"<option value='{p['id']}'>{html.escape(p['name'])} | {html.escape(p['sku'])} | {html.escape(p['barcode'])} | Stock:{p['stock']}</option>" for p in products])
        client_options = "".join([f"<option value='{c['id']}'>{html.escape(c['name'])}</option>" for c in clients])

        body = f"""
<h2>Nueva venta</h2>
<form method='post' action='/sales/new'>
<label>Cliente</label>
<select name='client_id'><option value=''>Consumidor final</option>{client_options}</select>
<label>Método de pago</label>
<select name='payment_method'><option>Efectivo</option><option>Tarjeta</option><option>Transferencia</option><option>Mixto</option></select>
<div id='lines'></div>
<button type='button' onclick='addLine()'>+ Agregar línea</button>
<button type='submit'>Cobrar y generar factura</button>
</form>
<template id='line-template'><div class='line'><select name='product_id'>{product_options}</select><input type='number' name='qty' min='1' value='1'></div></template>
<script>function addLine(){{const t=document.getElementById('line-template').content.cloneNode(true);document.getElementById('lines').appendChild(t);}}addLine();</script>
"""
        self._send_html(layout("Nueva venta", body))

    def create_sale(self):
        p = self._parse_post()
        product_ids = p.get("product_id", [])
        qtys = p.get("qty", [])
        client_id = p.get("client_id", [""])[0] or None
        payment = p.get("payment_method", ["Efectivo"])[0]
        if not product_ids:
            return self._redirect("/sales/new")

        conn = db_conn()
        lines = []
        subtotal = 0.0
        try:
            for pid, q in zip(product_ids, qtys):
                qty = max(1, int(q))
                prod = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
                if not prod or prod["stock"] < qty:
                    conn.close()
                    return self._redirect("/sales/new")
                lt = prod["price"] * qty
                subtotal += lt
                lines.append((prod, qty, lt))

            tax = round(subtotal * TAX_RATE, 2)
            total = round(subtotal + tax, 2)
            cur = conn.execute(
                "INSERT INTO sales(created_at, client_id, subtotal, tax, total, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), client_id, subtotal, tax, total, payment),
            )
            sale_id = cur.lastrowid
            for prod, qty, lt in lines:
                conn.execute("INSERT INTO sale_items(sale_id, product_id, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?)", (sale_id, prod["id"], qty, prod["price"], lt))
                conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, prod["id"]))
            conn.commit()
        finally:
            conn.close()
        self._redirect(f"/invoices/{sale_id}")

    def show_invoice(self, sale_id: int):
        conn = db_conn()
        sale = conn.execute(
            "SELECT s.*, c.name client_name, c.document client_document FROM sales s LEFT JOIN clients c ON c.id=s.client_id WHERE s.id=?",
            (sale_id,),
        ).fetchone()
        items = conn.execute(
            "SELECT si.*, p.name, p.sku, p.size, p.color FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=?",
            (sale_id,),
        ).fetchall()
        conn.close()

        if not sale:
            return self._send_html(layout("Factura", "No existe"), 404)
        rows = "".join([f"<tr><td>{html.escape(i['name'])} ({html.escape(i['sku'])})</td><td>{i['qty']}</td><td>${i['unit_price']:.2f}</td><td>${i['line_total']:.2f}</td></tr>" for i in items])
        body = f"""
<h2>Factura #{sale['id']}</h2>
<p><b>Fecha:</b> {sale['created_at']}</p>
<p><b>Cliente:</b> {html.escape(sale['client_name'] or 'Consumidor final')}</p>
<table><tr><th>Producto</th><th>Cant</th><th>Vlr unit</th><th>Total</th></tr>{rows}</table>
<p><b>Subtotal:</b> ${sale['subtotal']:.2f}</p>
<p><b>Impuesto:</b> ${sale['tax']:.2f}</p>
<p><b>Total:</b> ${sale['total']:.2f}</p>
<p><b>Método de pago:</b> {html.escape(sale['payment_method'])}</p>
<button onclick='window.print()'>Imprimir tirilla</button>
"""
        self._send_html(layout(f"Factura {sale_id}", body))


def run():
    init_db()
    server = HTTPServer((HOST, PORT), POSHandler)
    print(f"POS ejecutándose en http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
