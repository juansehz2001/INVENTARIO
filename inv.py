from flask import Blueprint, render_template, session, flash, redirect, url_for
from conexion import get_connection
import psycopg2.extras
from datetime import datetime

inv_bp = Blueprint("inventario", __name__, template_folder="templates")

def is_logged_in():
    from app import SESSION_TIMEOUT
    if "usuario" not in session:
        return False
    last_activity = session.get("last_activity")
    now = datetime.utcnow().timestamp()
    if last_activity and (now - last_activity) > SESSION_TIMEOUT:
        session.clear()
        return False
    session["last_activity"] = now
    return True

@inv_bp.route("/inventarioarticulo")
def inventario_articulo():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    rol_id = session.get("rol_id", 0)

    inventario = []
    articulos = []

    try:
        conn = get_connection()
        if conn is None:
            flash("Error de conexión a la base de datos", "danger")
            return redirect(url_for("home"))

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Tabla Inventario
        cur.execute("""
            SELECT a.id, a.nombre, a.descripcion, i.cantidad 
            FROM articulo a
            LEFT JOIN inv i ON a.id=i.idarticulo
            ORDER BY a.id
        """)
        inventario = cur.fetchall()

        # Tabla Artículos
        cur.execute("""
            SELECT id, nombre, descripcion 
            FROM articulo
            ORDER BY id
        """)
        articulos = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Error cargando inventario/artículos: {e}", "danger")

    return render_template(
        "inventarioarticulo.html",
        rol_id=rol_id,
        inventario=inventario,
        articulos=articulos
        
    )
