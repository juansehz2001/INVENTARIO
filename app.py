from flask import Flask, render_template, request, redirect, url_for, session, flash 
import psycopg2.extras 
from datetime import datetime
from conexion import get_connection
import logging

app = Flask(__name__)
app.secret_key = "3016898140"  

# Tiempo máximo de inactividad (10 min)
SESSION_TIMEOUT = 600  # segundos (10 min)

# ----------------- LOGGING GLOBAL -------------------
# Los logs se muestran en consola y se guardan en archivo logs_app.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # consola
        logging.FileHandler("logs_app.log", encoding="utf-8")  # archivo
    ]
)
def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

@app.before_request
def log_request_info():
    """Se ejecuta ANTES de cada request (cubre todo lo actual y futuro)."""
    user = session.get("usuario", "ANÓNIMO")
    rol = session.get("rol", "SIN ROL")
    ip = get_client_ip()
    method = request.method
    path = request.path

    app.logger.info(f"Usuario: {user} | Rol: {rol}  | {method} {path}")


# ----------------- LOGIN -------------------
@app.route("/", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        if conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query = """SELECT u.id, u.username , u.rol_id, r.descripcion AS rol 
                       FROM users u 
                       JOIN rol r ON u.rol_id = r.id
                       WHERE u.username = %s AND u.password = %s"""
            cur.execute(query, (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                session["usuario"] = user["username"]
                session["rol"] = user["rol"]
                session["rol_id"] = user["rol_id"]
                session["last_activity"] = datetime.utcnow().timestamp()
                flash("Inicio de sesión exitoso ", "success")
                return redirect(url_for("home"))
            else:
                flash("Usuario o contraseña incorrectos ", "danger")
    return render_template("login.html")


# ----------------- HOME -------------------
@app.route("/home")
def home():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión ", "warning")
        return redirect(url_for("login"))

    return render_template("home.html", 
                           usuario=session["usuario"], 
                           rol=session["rol"],
                           rol_id=session["rol_id"])


# ----------------- INVENTARIO ARTÍCULOS -------------------



# ----------------- INVENTARIO EQUIPOS -------------------
@app.route("/inventarioequipos")
def inventario_equipos():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión ", "warning")
        return redirect(url_for("login"))
    return render_template("inventarioequipos.html")


# ----------------- LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente ", "info")
    return redirect(url_for("login"))


# ----------------- CONTROL DE SESIÓN -------------------
def is_logged_in():
    """Valida que exista sesión y que no esté expirada."""
    if "usuario" not in session:
        return False

    last_activity = session.get("last_activity")
    now = datetime.utcnow().timestamp()

    if last_activity and (now - last_activity) > SESSION_TIMEOUT:
        session.clear()
        return False

    # refrescar actividad
    session["last_activity"] = now
    return True
from inv import inv_bp
app.register_blueprint(inv_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
