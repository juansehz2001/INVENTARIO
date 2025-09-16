from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from conexion import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
import random, string
import psycopg2.extras
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pywhatkit as kit
import datetime

adminuser_bp = Blueprint("adminuser", __name__, template_folder="templates")

# -------------------------
# CONFIGURACIONES NOTIFICACIÓN
# -------------------------
# Gmail
REMITENTE = "juanseh888@gmail.com"
PASSWORD = "rfmu hrvm hfzl guxs"

# Telegram
TELEGRAM_TOKEN = "8079982879:AAHJLsulQEAsb1iuavEXbf3XEPa4xxtIWFY"


# -------------------------
# FUNCIONES DE ENVÍO
# -------------------------
def enviar_email(destinatario, asunto, mensaje):
    try:
        msg = MIMEMultipart()
        msg["From"] = REMITENTE
        msg["To"] = destinatario
        msg["Subject"] = asunto
        msg.attach(MIMEText(mensaje, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(REMITENTE, PASSWORD)
            server.sendmail(REMITENTE, destinatario, msg.as_string())

        return True
    except Exception as e:
        print("Error correo:", e)
        return False


def enviar_telegram(chat_id, mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": mensaje}
        r = requests.post(url, data=data)
        return r.status_code == 200
    except Exception as e:
        print("Error telegram:", e)
        return False


def enviar_whatsapp(numero, mensaje):
    try:
        # Agregar prefijo internacional si no lo tiene
        if not numero.startswith("+"):
            numero = "+57" + numero

        hora = datetime.datetime.now().hour
        minuto = datetime.datetime.now().minute + 1  # se agenda un minuto después
        kit.sendwhatmsg(numero, mensaje, hora, minuto)
        return True
    except Exception as e:
        print("Error WhatsApp:", e)
        return False


# -------------------------
# RUTAS
# -------------------------

# Ruta principal
@adminuser_bp.route("/adminuser")
def admin_user():
    if "usuario" not in session:
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("home"))

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT u.id, u.username, u.rol_id, r.telefono, r.correo, r.telegram, ro.descripcion as rol
        FROM users u
        LEFT JOIN record r ON u.idrecord = r.id
        LEFT JOIN rol ro ON u.rol_id = ro.id
    """)
    usuarios = cur.fetchall()

    cur.execute("SELECT id, descripcion FROM rol")
    roles = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "adminuser.html",
        usuario=session["usuario"],
        rol=session["rol"],
        usuarios=usuarios,
        roles=roles
    )


# Registrar usuario
@adminuser_bp.route("/adminuser/registrar", methods=["POST"])
def registrar_usuario():
    username = request.form["username"]
    password = request.form["password"]
    rol_id = request.form["rol_id"]
    telefono = request.form.get("telefono")
    correo = request.form.get("correo")
    telegram = request.form.get("telegram")

    hashed_password = generate_password_hash(password)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "INSERT INTO record (telefono, correo, telegram) VALUES (%s, %s, %s) RETURNING id",
        (telefono, correo, telegram)
    )
    record_id = cur.fetchone()["id"]

    cur.execute(
        """
        INSERT INTO users (username, password, rol_id, credential_id, public_key, sign_count, idrecord)
        VALUES (%s, %s, %s, NULL, NULL, NULL, %s)
        """,
        (username, hashed_password, rol_id, record_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Usuario registrado correctamente", "success")
    return redirect(url_for("adminuser.admin_user"))


# Cambiar contraseña
@adminuser_bp.route("/adminuser/cambiar", methods=["POST"])
def cambiar_contrasena():
    user_id = request.form["user_id"]
    actual = request.form["actual"]
    nueva = request.form["nueva"]
    confirmar = request.form["confirmar"]

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT password FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    if not user or not check_password_hash(user["password"], actual):
        flash("❌ Contraseña actual incorrecta", "danger")
    elif nueva != confirmar:
        flash("❌ La nueva contraseña no coincide", "danger")
    else:
        hashed = generate_password_hash(nueva)
        cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
        conn.commit()
        flash("✅ Contraseña actualizada", "success")

    cur.close()
    conn.close()
    return redirect(url_for("adminuser.admin_user"))


# Recordar contraseña
@adminuser_bp.route("/adminuser/recordar", methods=["POST"])
def recordar_contrasena():
    user_id = request.form["user_id"]
    metodo = request.form["metodo"]  # correo / whatsapp / telegram

    nueva = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    hashed = generate_password_hash(nueva)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
    conn.commit()

    cur.execute("""
        SELECT r.telefono, r.correo, r.telegram
        FROM users u
        LEFT JOIN record r ON u.idrecord = r.id
        WHERE u.id=%s
    """, (user_id,))
    datos = cur.fetchone()

    cur.close()
    conn.close()

    enviado = False
    mensaje = f"🔐 Tu nueva contraseña es: {nueva}"

    if metodo == "correo" and datos["correo"]:
        enviado = enviar_email(datos["correo"], "Recuperación de contraseña", mensaje)
    elif metodo == "telegram" and datos["telegram"]:
        enviado = enviar_telegram(datos["telegram"], mensaje)
    elif metodo == "whatsapp" and datos["telefono"]:
        enviado = enviar_whatsapp(datos["telefono"], mensaje)

    if enviado:
        flash(f"✅ Nueva contraseña enviada por {metodo.upper()}", "success")
    else:
        flash(f"❌ No se pudo enviar la contraseña por {metodo.upper()}", "danger")

    return redirect(url_for("adminuser.admin_user"))
