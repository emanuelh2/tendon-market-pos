
from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "tendon_secret_key"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS producto (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    precio REAL,
                    stock INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS detalle_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER,
                    id_producto INTEGER,
                    cantidad INTEGER)''')

    c.execute("INSERT OR IGNORE INTO usuario (id, username, password) VALUES (1, 'admin', '1234')")
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM usuario WHERE username=? AND password=?",
                            (username, password)).fetchone()
        conn.close()
        if user:
            session["user"] = username
            return redirect("/dashboard")
    return '''
    <h2>Login POS</h2>
    <form method="post">
        Usuario: <input name="username"><br>
        Contraseña: <input name="password" type="password"><br>
        <button>Ingresar</button>
    </form>
    '''

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    conn = get_db()
    productos = conn.execute("SELECT * FROM producto").fetchall()
    conn.close()
    html = "<h2>Inventario</h2>"
    html += "<a href='/agregar'>Agregar Producto</a><br><br>"
    html += "<a href='/vender'>Registrar Venta</a><br><br>"
    for p in productos:
        html += f"{p['nombre']} - Precio: {p['precio']} - Stock: {p['stock']}<br>"
    return html

@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        conn = get_db()
        conn.execute("INSERT INTO producto (nombre, precio, stock) VALUES (?, ?, ?)",
                     (nombre, precio, stock))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return '''
    <h2>Agregar Producto</h2>
    <form method="post">
        Nombre: <input name="nombre"><br>
        Precio: <input name="precio"><br>
        Stock: <input name="stock"><br>
        <button>Guardar</button>
    </form>
    '''

@app.route("/vender", methods=["GET", "POST"])
def vender():
    conn = get_db()
    productos = conn.execute("SELECT * FROM producto").fetchall()

    if request.method == "POST":
        id_producto = request.form["producto"]
        cantidad = int(request.form["cantidad"])

        producto = conn.execute("SELECT * FROM producto WHERE id=?",
                                (id_producto,)).fetchone()

        if producto and producto["stock"] >= cantidad:
            nuevo_stock = producto["stock"] - cantidad
            total = producto["precio"] * cantidad

            conn.execute("UPDATE producto SET stock=? WHERE id=?",
                         (nuevo_stock, id_producto))
            conn.execute("INSERT INTO venta (total) VALUES (?)", (total,))
            conn.commit()

        conn.close()
        return redirect("/dashboard")

    html = "<h2>Registrar Venta</h2>"
    html += "<form method='post'>"
    html += "Producto: <select name='producto'>"
    for p in productos:
        html += f"<option value='{p['id']}'>{p['nombre']}</option>"
    html += "</select><br>"
    html += "Cantidad: <input name='cantidad'><br>"
    html += "<button>Vender</button></form>"
    conn.close()
    return html

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
