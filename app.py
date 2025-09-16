from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2.extras 
from datetime import datetime
from conexion import get_connection
import logging
import base64
import cbor2
import os
from adminuser import adminuser_bp
from inv import inv_bp
from huella import huella_bp
from invequip import invequip_bp
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
import struct
import json
from werkzeug.security import check_password_hash
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

def b64url_encode(data: bytes) -> str:
    """Convierte bytes a base64url sin padding"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

@app.after_request
def add_ngrok_header(response):
    # Agrega el header para que ngrok no muestre la advertencia
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response
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

    # -----------------------
# 🔑 Utilidad: COSE → EC
# -----------------------
def cose_to_ec_public_key(cose_key: dict):
    """
    Convierte un COSE_Key (EC2 P-256) a EllipticCurvePublicKey usable en Python.
    """
    if cose_key.get(3) != -7:
        raise ValueError("Algoritmo no soportado (solo ES256)")

    x_bytes = cose_key[-2]
    y_bytes = cose_key[-3]

    if not (isinstance(x_bytes, bytes) and isinstance(y_bytes, bytes)):
        raise ValueError("Formato COSE inválido")

    uncompressed_point = b"\x04" + x_bytes + y_bytes
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), uncompressed_point)


@huella_bp.route("/huella/generate_challenge", methods=["POST"])
def huella_generate_challenge():
    content = request.json
    username = content.get("username")
    if not username:
        return jsonify({"error": "Falta el username"}), 400

    # Generar challenge aleatorio (32 bytes)
    challenge = os.urandom(32)
    challenge_b64url = b64url_encode(challenge)

    # Guardar en sesión
    session["webauthn_challenge"] = challenge_b64url
    session["webauthn_username"] = username

    # Recuperar credential_id del usuario
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT credential_id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not user["credential_id"]:
        return jsonify({"error": "Usuario no tiene huella registrada"}), 400

    credential_id_b64url = b64url_encode(user["credential_id"])

    return jsonify({
        "challenge": challenge_b64url,
        "credential_id": credential_id_b64url
    })

@app.route("/huella/login_verify", methods=["POST"])
def huella_login_verify():
    conn = None
    cur = None
    try:
        content = request.json
        username = content.get("username")
        auth_data = base64.b64decode(content["auth_data"])
        client_data = base64.b64decode(content["client_data"])
        signature = base64.b64decode(content["signature"])

        # -----------------------
        # Validar username y challenge
        # -----------------------
        expected_username = session.get("webauthn_username")
        expected_challenge = session.get("webauthn_challenge")

        if username != expected_username or not expected_challenge:
            return jsonify({"error": "Sesión o challenge inválido"}), 400

        # -----------------------
        # Parsear clientDataJSON
        # -----------------------
        client_data_json = json.loads(client_data.decode("utf-8"))

        if client_data_json.get("type") != "webauthn.get":
            return jsonify({"error": "Tipo de clientData inválido"}), 400

        if client_data_json.get("challenge") != expected_challenge:
            return jsonify({"error": "Challenge inválido"}), 400

        origin = client_data_json.get("origin", "")
        if not origin.endswith(".ngrok-free.app"):
         return jsonify({"error": f"Origen inválido: {origin}"}), 400

        # -----------------------
        # Recuperar clave pública y sign_count de BD
        # -----------------------
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.public_key, u.sign_count, u.rol_id, r.descripcion AS rol
            FROM users u
            JOIN rol r ON u.rol_id = r.id
            WHERE u.username = %s
        """, (username,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        public_key_cose = cbor2.loads(user["public_key"])
        public_key = cose_to_ec_public_key(public_key_cose)

        # -----------------------
        # Construir signed_data y verificar firma
        # -----------------------
        digest = hashes.Hash(hashes.SHA256())
        digest.update(client_data)
        client_data_hash = digest.finalize()
        signed_data = auth_data + client_data_hash

        public_key.verify(signature, signed_data, ec.ECDSA(hashes.SHA256()))

        # -----------------------
        # Validar y actualizar sign_count
        # -----------------------
        sign_count_new = struct.unpack(">I", auth_data[33:37])[0]

        if sign_count_new <= user["sign_count"]:
            return jsonify({"error": "Firma replay detectada"}), 400

        cur.execute("UPDATE users SET sign_count = %s WHERE username = %s", (sign_count_new, username))
        conn.commit()

        # -----------------------
        # Login exitoso: crear sesión
        # -----------------------
        session["usuario"] = username
        session["rol"] = user["rol"]
        session["rol_id"] = user["rol_id"]
        session.pop("webauthn_challenge", None)
        session.pop("webauthn_username", None)

        logging.info(f"Usuario: {username} | Rolid: {user['rol_id']} | Rol: {user['rol']}  | LOGIN con huella")
        return jsonify({"success": True})

    except InvalidSignature:
        return jsonify({"error": "Firma inválida"}), 401
    except Exception as e:
        logging.error(f"Error en huella_login_verify: {e}")
        return jsonify({"error": str(e)}), 400
    finally:
        if cur: cur.close()
        if conn: conn.close()


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

            # 🔹 Buscar usuario solo por username
            query = """
                SELECT u.id, u.username, u.password, u.rol_id, r.descripcion AS rol
                FROM users u
                JOIN rol r ON u.rol_id = r.id
                WHERE u.username = %s
            """
            cur.execute(query, (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            # 🔹 Validar contraseña encriptada
            if user and check_password_hash(user["password"], password):
                session["usuario"] = user["username"]
                session["rol"] = user["rol"]
                session["rol_id"] = user["rol_id"]
                session["last_activity"] = datetime.utcnow().timestamp()
                flash("Inicio de sesión exitoso ✅", "success")
                return redirect(url_for("home"))
            else:
                flash("Usuario o contraseña incorrectos ❌", "danger")

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


# ----------------- BLUEPRINTS -------------------
app.register_blueprint(inv_bp)
app.register_blueprint(huella_bp)
app.register_blueprint(adminuser_bp)
app.register_blueprint(invequip_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
