from flask import Blueprint, render_template, session, flash, redirect, url_for, request
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
    bajas = []

    try:
        conn = get_connection()
        if conn is None:
            flash("Error de conexión a la base de datos", "danger")
            return redirect(url_for("home"))

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Tabla Inventario
        cur.execute("""
            SELECT a.id, a.nombre, a.descripcion, COALESCE(i.cantidad,0) AS cantidad
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

        # Tabla Bajas
        cur.execute("""
            SELECT i.id, i.idarticulo, a.nombre, i.cantidad, i.descripcion, i.fecha, i.tipo
            FROM invbaja i 
            INNER JOIN articulo a ON i.idarticulo=a.id 
            ORDER BY i.id desc
        """)
        bajas = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Error cargando inventario/artículos/bajas: {e}", "danger")

    return render_template(
        "inventarioarticulo.html",
        rol_id=rol_id,
        inventario=inventario,
        articulos=articulos,
        bajas=bajas
    )

# 🔹 Inventario
@inv_bp.route("/agregar_inventario", methods=["POST"])
def agregar_inventario():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_idarticulo = int(request.form.get("idarticulo"))
        p_cantidad = int(request.form.get("cantidad"))
        p_motivo = request.form.get("motivo").strip()
        if p_cantidad <= 0 or not p_motivo:
            raise ValueError("Cantidad y motivo deben ser válidos")

        conn = get_connection()
        if conn is None:
            flash("Error de conexión a la base de datos", "danger")
            return redirect(url_for("inventario.inventario_articulo"))

        cur = conn.cursor()
        cur.execute("SELECT agregar_inventario(%s, %s, %s);",
                    (p_idarticulo, p_cantidad, p_motivo))
        conn.commit()
        flash("Inventario actualizado correctamente ✅", "success")
    except Exception as e:
        flash(f"Error al agregar inventario: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))

@inv_bp.route("/eliminar_inventario", methods=["POST"])
def eliminar_inventario():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_idarticulo = int(request.form.get("idarticulo"))
        p_cantidad = int(request.form.get("cantidad"))
        p_motivo = request.form.get("motivo").strip()
        if p_cantidad <= 0 or not p_motivo:
            raise ValueError("Cantidad y motivo deben ser válidos")

        conn = get_connection()
        if conn is None:
            flash("Error de conexión a la base de datos", "danger")
            return redirect(url_for("inventario.inventario_articulo"))

        cur = conn.cursor()
        cur.execute("SELECT eliminar_inventario(%s, %s, %s);",
                    (p_idarticulo, p_cantidad, p_motivo))
        conn.commit()
        flash("Inventario reducido correctamente 🗑️", "success")
    except Exception as e:
        flash(f"Error al eliminar inventario: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))

# 🔹 Artículos
@inv_bp.route("/agregar_articulo", methods=["POST"])
def agregar_articulo():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        nombre = request.form.get("nombre").strip()
        descripcion = request.form.get("descripcion").strip()
        if not nombre or not descripcion:
            raise ValueError("Nombre y descripción son obligatorios")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT agregar_articulo(%s, %s);", (nombre, descripcion))
        conn.commit()
        flash("Artículo agregado correctamente ✅", "success")
    except Exception as e:
        flash(f"Error al agregar artículo: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))

@inv_bp.route("/actualizar_articulo", methods=["POST"])
def actualizar_articulo():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_id = int(request.form.get("id"))
        nombre = request.form.get("nombre").strip()
        descripcion = request.form.get("descripcion").strip()
        if not nombre or not descripcion:
            raise ValueError("Nombre y descripción son obligatorios")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT actualizar_articulo(%s, %s, %s);", (p_id, nombre, descripcion))
        conn.commit()
        flash("Artículo actualizado correctamente ✏️", "success")
    except Exception as e:
        flash(f"Error al actualizar artículo: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))

@inv_bp.route("/eliminar_articulo", methods=["POST"])
def eliminar_articulo():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_id = int(request.form.get("id"))
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT eliminar_articulo(%s);", (p_id,))
        conn.commit()
        flash("Artículo eliminado correctamente 🗑️", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el artículo: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))
# 🔹 Historial Inventario - Editar
@inv_bp.route("/editar_historial", methods=["POST"])
def editar_historial():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_idarticulo = int(request.form.get("id"))
        p_tipo = request.form.get("tipo").strip()
        p_nueva_cantidad = int(request.form.get("cantidad"))
        p_nueva_descripcion = request.form.get("descripcion").strip()

        # Validaciones
        if p_nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        if not p_nueva_descripcion:
            raise ValueError("La descripción no puede estar vacía")
        if p_tipo not in ('NUEVO ARTICULO','AGREGAR INVENTARIO','BAJA ARTICULO'):
            raise ValueError(f"Tipo inválido: {p_tipo}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT editar_historial(%s, %s, %s);",
                    (p_idarticulo, p_nueva_descripcion, p_nueva_cantidad))
        conn.commit()
        flash("Registro editado correctamente ✏️", "success")

    except Exception as e:
        flash(f"No se pudo editar el registro: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))

# 🔹 Historial Inventario - Eliminar
@inv_bp.route("/eliminar_historial", methods=["POST"])
def eliminar_historial():
    if not is_logged_in():
        flash("Sesión expirada. Vuelve a iniciar sesión", "warning")
        return redirect(url_for("login"))

    try:
        p_id = int(request.form.get("id"))
        p_tipo = request.form.get("tipo").strip()

        # Validaciones
        if p_tipo not in ('NUEVO ARTICULO','AGREGAR INVENTARIO','BAJA ARTICULO'):
            raise ValueError(f"Tipo inválido: {p_tipo}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT eliminar_historial(%s);", (p_id,))
        conn.commit()
        flash("Registro eliminado correctamente 🗑️", "success")

    except Exception as e:
        flash(f"No se pudo eliminar el registro: {e}", "danger")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return redirect(url_for("inventario.inventario_articulo"))
