from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from conexion import get_connection
import psycopg2

invequip_bp = Blueprint("invequip", __name__, template_folder="templates")

@invequip_bp.route("/inventario_equipos")
def inventario_equipos():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))
    
       
    conn = get_connection()
    cur = conn.cursor()

    # Consulta principal: almacenamiento con características
    cur.execute("""
        SELECT a.id, ac.id AS id_carac, a.idequipo, a.marca, a.horas_uso,
               a.estado, a.baja, ac.capacidad, ac.tipo
        FROM almacenamiento a
        INNER JOIN almacenamientocarac ac ON a.idalmacenamientocarac = ac.id
        where a.baja = false
        ORDER BY a.id;
    """)
    registros = cur.fetchall()
    cur.execute("SELECT id, codigo FROM equipo ORDER BY codigo;")
    equipos = cur.fetchall()
    cur.execute("SELECT id, capacidad, tipo FROM almacenamientocarac ORDER BY id;")
    caracteristicas = cur.fetchall()



    # Consulta de bajas
    cur.execute("""
        SELECT b.id, b.idregistro,b.tabla, b.descripcion, b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'almacenamiento'
        ORDER BY b.id DESC;
    """)
    bajas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("inventarioequipos.html",
                           usuario=session["usuario"],
                           rol=session["rol"],
                           rol_id=session["rol_id"],
                           registros=registros,
                           bajas=bajas
                           , equipos=equipos,
                       caracteristicas=caracteristicas)


# Ejecutar sp_baja_almacenamiento
@invequip_bp.route("/almacenamiento/baja/<int:id>", methods=["POST"])
def baja_almacenamiento(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_baja_almacenamiento(%s, %s, %s)", (id, descripcion, fecha_baja))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="almacenamiento"))

# Ejecutar sp_revertir_baja_almacenamiento
@invequip_bp.route("/almacenamiento/revertir/<int:id>", methods=["POST"])
def revertir_baja_almacenamiento(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_revertir_baja_almacenamiento(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="almacenamiento"))
# =========================
# NUEVA CARACTERÍSTICA
# =========================
@invequip_bp.route("/almacenamiento/nueva_caracteristica", methods=["POST"])
def nueva_caracteristica():
    capacidad = request.form.get("capacidad")
    tipo = request.form.get("tipo")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_insert_almacenamientocarac(%s, %s)", (capacidad, tipo))
        conn.commit()
        flash("Característica registrada correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar característica: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="almacenamiento"))


# =========================
# NUEVO ALMACENAMIENTO
# =========================
@invequip_bp.route("/almacenamiento/nuevo", methods=["POST"])
def nuevo_almacenamiento():
    id_carac = request.form.get("id_carac")
    id_equipo = None
    marca = request.form.get("marca")
    horas_uso = request.form.get("horas_uso") or None  # puede venir vacío
    estado = request.form.get("estado")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL sp_insert_almacenamiento(%s, %s, %s, %s, %s)",
            (id_carac, id_equipo, marca, horas_uso, estado),
        )
        conn.commit()
        flash("Almacenamiento registrado correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar almacenamiento: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="almacenamiento"))
# =========================
# ACTUALIZAR ALMACENAMIENTO
# =========================
@invequip_bp.route("/almacenamiento/actualizar/<int:id>", methods=["POST"])
def actualizar_almacenamiento(id):
    id_equipo = request.form.get("id_equipo")or None
    marca = request.form.get("marca")
    horas_uso = request.form.get("horas_uso") or None
    estado = request.form.get("estado")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE almacenamiento
            SET idequipo = %s, marca = %s, horas_uso = %s, estado = %s
            WHERE id = %s
        """, (id_equipo, marca, horas_uso, estado, id))
        conn.commit()
        flash(f"Registro {id} actualizado correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="almacenamiento"))
