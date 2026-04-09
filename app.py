"""
CFC Store - Sistema de Ventas Local
Ejecutar: python app.py
Luego abrir: http://127.0.0.1:5000
"""

import os
import sqlite3
import webbrowser
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
# Decide dónde guardar los datos (base de datos).
# - Si está definida la variable de entorno CFC_STORE_DATA_DIR se usa esa ruta.
# - En Windows, por defecto se usa %LOCALAPPDATA%/CFC_STORE.
# - En otros sistemas se usa la carpeta del script (comportamiento previo).
data_dir_env = os.environ.get("CFC_STORE_DATA_DIR")
if data_dir_env:
    BASE_DIR = os.path.abspath(data_dir_env)
else:
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        BASE_DIR = os.path.join(local_appdata, "CFC_STORE")
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asegurarse que la carpeta existe y el archivo DB será creado allí
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ─── Inicialización de la base de datos ───────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            codigo_barra TEXT,
            precio      INTEGER NOT NULL,
            categoria   TEXT NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0,
            activo      INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha          TEXT NOT NULL,
            total          INTEGER NOT NULL,
            metodo_pago    TEXT NOT NULL,
            monto_recibido INTEGER,
            vuelto         INTEGER,
            descuento      INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id         INTEGER NOT NULL REFERENCES ventas(id),
            producto_id      INTEGER NOT NULL REFERENCES productos(id),
            nombre_producto  TEXT NOT NULL,
            cantidad         INTEGER NOT NULL,
            precio_unitario  INTEGER NOT NULL
        );
    """)

    # Insertar productos de muestra si la tabla está vacía
    count = c.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if count == 0:
        productos = [
            ("Biblia RVR60 Letra Grande",   "9780829766103", 24990, "Biblias",   15),
            ("Biblia NVI Tapa Dura",         "9780829759396", 29990, "Biblias",   10),
            ("Biblia TLA Ilustrada",         "9780829751246", 19990, "Biblias",    8),
            ("Biblia DHH Bolsillo",          "9780829741414", 12990, "Biblias",   12),
            ("Biblia RVR60 Infantil",        "9780829782912", 18990, "Biblias",    6),
            ("Cuaderno Universitario 100h",  "7802900123456",  2990, "Papelería", 50),
            ("Cuaderno Espiral A4 80h",      "7802900123457",  1990, "Papelería", 40),
            ("Cuaderno Tapa Dura Pequeño",   "7802900123458",  3490, "Papelería", 25),
            ("Lápiz Grafito HB (x6)",        "7801234567890",   990, "Papelería", 60),
            ("Lápices de Colores 12 un",     "7801234567891",  2490, "Papelería", 35),
            ("Destacadores x3 Colores",      "7801234567892",  1590, "Papelería", 30),
            ("Bolígrafo Azul (x3)",          "7801234567893",   890, "Papelería", 55),
            ("Polera 'Fe' Blanca Talla M",   None,            12990, "Vestuario",  8),
            ("Polera 'Fe' Blanca Talla L",   None,            12990, "Vestuario",  6),
            ("Polera 'Amor' Negra Talla S",  None,            13990, "Vestuario",  5),
            ("Botella 500ml Acero CFC",      "7809876543210",  9990, "Accesorios",20),
            ("Botella 1L Vidrio Templado",   "7809876543211", 14990, "Accesorios",12),
            ("Post-it 100 hojas Amarillo",   "7805555001122",  1990, "Oficina",   40),
            ("Clips Metálicos x100",         "7805555001123",   690, "Oficina",   45),
            ("Tijeras Punta Redonda",        "7805555001124",  2190, "Oficina",   18),
        ]
        c.executemany(
            "INSERT INTO productos (nombre, codigo_barra, precio, categoria, stock) VALUES (?,?,?,?,?)",
            productos
        )

    conn.commit()
    conn.close()

# ─── Helpers ──────────────────────────────────────────────────────────────────

def fmt_clp(valor):
    return f"${valor:,.0f}".replace(",", ".")

# ─── Rutas principales ────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("ventas"))

@app.route("/ventas")
def ventas():
    return render_template("ventas.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ─── API Productos ────────────────────────────────────────────────────────────

@app.route("/api/productos", methods=["GET"])
def api_productos():
    q = request.args.get("q", "").strip()
    conn = get_db()
    if q:
        rows = conn.execute(
            "SELECT * FROM productos WHERE activo=1 AND (nombre LIKE ? OR codigo_barra=?)",
            (f"%{q}%", q)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM productos WHERE activo=1 ORDER BY categoria, nombre").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/productos/<int:pid>", methods=["GET"])
def api_producto(pid):
    conn = get_db()
    row = conn.execute("SELECT * FROM productos WHERE id=? AND activo=1", (pid,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "No encontrado"}), 404

@app.route("/api/productos", methods=["POST"])
def api_crear_producto():
    data = request.json
    conn = get_db()
    conn.execute(
        "INSERT INTO productos (nombre, codigo_barra, precio, categoria, stock) VALUES (?,?,?,?,?)",
        (data["nombre"], data.get("codigo_barra") or None, int(data["precio"]),
         data["categoria"], int(data["stock"]))
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/productos/<int:pid>", methods=["PUT"])
def api_editar_producto(pid):
    data = request.json
    conn = get_db()
    conn.execute(
        "UPDATE productos SET nombre=?, codigo_barra=?, precio=?, categoria=?, stock=? WHERE id=?",
        (data["nombre"], data.get("codigo_barra") or None, int(data["precio"]),
         data["categoria"], int(data["stock"]), pid)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/productos/<int:pid>", methods=["DELETE"])
def api_eliminar_producto(pid):
    conn = get_db()
    conn.execute("UPDATE productos SET activo=0 WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ─── API Ventas ───────────────────────────────────────────────────────────────

@app.route("/api/ventas", methods=["POST"])
def api_registrar_venta():
    data = request.json
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "Carrito vacío"}), 400

    conn = get_db()
    try:
        # Verificar stock
        for item in items:
            prod = conn.execute("SELECT stock FROM productos WHERE id=?", (item["id"],)).fetchone()
            if not prod or prod["stock"] < item["cantidad"]:
                conn.close()
                return jsonify({"error": f"Stock insuficiente para producto ID {item['id']}"}), 400

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = int(data["total"])
        descuento = int(data.get("descuento", 0))
        metodo = data["metodo_pago"]
        recibido = int(data.get("monto_recibido", total))
        vuelto = max(0, recibido - total)

        cur = conn.execute(
            "INSERT INTO ventas (fecha, total, metodo_pago, monto_recibido, vuelto, descuento) VALUES (?,?,?,?,?,?)",
            (fecha, total, metodo, recibido, vuelto, descuento)
        )
        venta_id = cur.lastrowid

        for item in items:
            conn.execute(
                "INSERT INTO detalle_ventas (venta_id, producto_id, nombre_producto, cantidad, precio_unitario) VALUES (?,?,?,?,?)",
                (venta_id, item["id"], item["nombre"], item["cantidad"], item["precio"])
            )
            conn.execute("UPDATE productos SET stock = stock - ? WHERE id=?", (item["cantidad"], item["id"]))

        conn.commit()
        conn.close()
        return jsonify({"ok": True, "venta_id": venta_id, "vuelto": vuelto})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/ventas/hoy", methods=["GET"])
def api_ventas_hoy():
    fecha_param = request.args.get("fecha", date.today().strftime("%Y-%m-%d"))
    conn = get_db()
    ventas = conn.execute(
        "SELECT v.*, GROUP_CONCAT(d.nombre_producto || ' x' || d.cantidad, ' | ') as detalle "
        "FROM ventas v LEFT JOIN detalle_ventas d ON v.id=d.venta_id "
        "WHERE DATE(v.fecha)=? GROUP BY v.id ORDER BY v.fecha DESC",
        (fecha_param,)
    ).fetchall()
    conn.close()
    return jsonify([dict(v) for v in ventas])

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    fecha_param = request.args.get("fecha", date.today().strftime("%Y-%m-%d"))
    conn = get_db()

    total_dia = conn.execute(
        "SELECT COALESCE(SUM(total),0) as total, COUNT(*) as transacciones FROM ventas WHERE DATE(fecha)=?",
        (fecha_param,)
    ).fetchone()

    por_metodo = conn.execute(
        "SELECT metodo_pago, SUM(total) as suma, COUNT(*) as cant FROM ventas WHERE DATE(fecha)=? GROUP BY metodo_pago",
        (fecha_param,)
    ).fetchall()

    top_producto = conn.execute(
        "SELECT d.nombre_producto, SUM(d.cantidad) as total_cant "
        "FROM detalle_ventas d JOIN ventas v ON d.venta_id=v.id "
        "WHERE DATE(v.fecha)=? GROUP BY d.nombre_producto ORDER BY total_cant DESC LIMIT 1",
        (fecha_param,)
    ).fetchone()

    ultimas = conn.execute(
        "SELECT v.id, v.fecha, v.total, v.metodo_pago, "
        "GROUP_CONCAT(d.nombre_producto || ' x' || d.cantidad, ' | ') as detalle "
        "FROM ventas v LEFT JOIN detalle_ventas d ON v.id=d.venta_id "
        "WHERE DATE(v.fecha)=? GROUP BY v.id ORDER BY v.fecha DESC LIMIT 10",
        (fecha_param,)
    ).fetchall()

    conn.close()

    total_val = total_dia["total"]
    trans = total_dia["transacciones"]
    ticket_prom = (total_val // trans) if trans > 0 else 0

    metodos = {r["metodo_pago"]: {"suma": r["suma"], "cant": r["cant"]} for r in por_metodo}

    return jsonify({
        "total_dia": total_val,
        "transacciones": trans,
        "ticket_promedio": ticket_prom,
        "top_producto": dict(top_producto) if top_producto else None,
        "por_metodo": metodos,
        "ultimas_ventas": [dict(v) for v in ultimas]
    })

# ─── Arranque ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n" + "="*50)
    print("  CFC Store iniciado correctamente")
    print(f"  Base de datos: {DB_PATH}")
    print("  Abre tu navegador en: http://127.0.0.1:5000")
    print("="*50 + "\n")
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
