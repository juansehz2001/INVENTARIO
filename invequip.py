from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from conexion import get_connection
import psycopg2
from psycopg2 import sql
from datetime import date

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

 # === Consulta usuarios con área, cargo y teléfono ===
    cur.execute("""
        SELECT u.id, u.cc, u.nombre, u.email, u.baja, 
               a.area, c.descripcion, t.numero
        FROM usuario u
        INNER JOIN cargo c ON u.idcargo = c.id
        INNER JOIN area a ON u.idarea = a.id
        LEFT JOIN telefono t ON t.idusuario = u.id
        ORDER BY u.id;
    """)
    usuarios = cur.fetchall()

    # === Consulta bajas de usuarios ===
    cur.execute("""
        SELECT b.id, b.idregistro, b.tabla, b.descripcion, 
               b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'usuario'
        ORDER BY b.id DESC;
    """)
    bajas_usuarios = cur.fetchall()

    # Consulta de bajas
    cur.execute("""
        SELECT b.id, b.idregistro,b.tabla, b.descripcion, b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'usuario'
        ORDER BY b.id DESC;
    """)
    bajas = cur.fetchall()
     # Consulta general ubicaciones (equipos + join ubicaciones)
    cur.execute("""
        select eq.id,eq.codigo,s.sede ,p.piso ,o.oficina_salon from equipo eq inner join sede s on s.id=eq.idsede
inner join piso p on p.id=eq.idpiso
inner join oficina o on o.id=eq.idoficina
        ORDER BY eq.id
    """)
    ubicaciones = cur.fetchall()

    # Listas individuales
    cur.execute("SELECT id, piso FROM piso ORDER BY id")
    pisos = cur.fetchall()
    cur.execute("SELECT id, sede FROM sede ORDER BY id")
    sedes = cur.fetchall()
    cur.execute("SELECT id, oficina_salon FROM oficina ORDER BY id")
    oficinas = cur.fetchall()

    # === Áreas ===
    cur.execute("SELECT id, area FROM area ORDER BY id;")
    areas = cur.fetchall()

    # === Cargos ===
    cur.execute("SELECT id, descripcion FROM cargo ORDER BY id;")
    cargos = cur.fetchall()

    # === Teléfonos ===
    cur.execute("""
        SELECT t.id, t.numero, u.nombre 
        FROM telefono t 
        LEFT JOIN usuario u ON u.id = t.idusuario
        ORDER BY t.id;
    """)
    telefonos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("inventarioequipos.html",
                           usuario=session["usuario"],
                           rol=session["rol"],
                           rol_id=session["rol_id"],
                           registros=registros,
                           bajas=bajas, 
                           equipos=equipos,
                           caracteristicas=caracteristicas,
                           ubicaciones=ubicaciones,
                           pisos=pisos,
                           sedes=sedes,
                           oficinas=oficinas,
                           usuarios=usuarios,
                           areas=areas,
                           cargos=cargos,
                           telefonos=telefonos,
                           bajas_usuarios=bajas_usuarios)


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
# --------------------------
# CRUD PISO
# --------------------------
@invequip_bp.route('/ubicacion/piso/nuevo', methods=['POST'])
def nuevo_piso():
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO piso (piso) VALUES (%s)", (nombre,))
    conn.commit()
    cur.close()
    conn.close()
    flash("✅ Piso creado con éxito.", "success")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/piso/actualizar/<int:id>', methods=['POST'])
def actualizar_piso(id):
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE piso SET piso=%s WHERE id=%s", (nombre, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("✏️ Piso actualizado.", "info")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/piso/eliminar/<int:id>', methods=['POST'])
def eliminar_piso(id):
    conn = get_connection()
    cur = conn.cursor()

    # Verificar si hay equipos asociados
    cur.execute("SELECT COUNT(*) FROM equipo WHERE idpiso=%s", (id,))
    count = cur.fetchone()[0]
    if count > 0:
        flash("❌ No se puede eliminar: existen equipos en este piso.", "danger")
    else:
        cur.execute("DELETE FROM piso WHERE id=%s", (id,))
        conn.commit()
        flash("🗑️ Piso eliminado.", "warning")

    cur.close()
    conn.close()
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


# --------------------------
# CRUD SEDE
# --------------------------
@invequip_bp.route('/ubicacion/sede/nuevo', methods=['POST'])
def nueva_sede():
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sede (sede) VALUES (%s)", (nombre,))
    conn.commit()
    cur.close()
    conn.close()
    flash("✅ Sede creada con éxito.", "success")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/sede/actualizar/<int:id>', methods=['POST'])
def actualizar_sede(id):
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE sede SET sede=%s WHERE id=%s", (nombre, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("✏️ Sede actualizada.", "info")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/sede/eliminar/<int:id>', methods=['POST'])
def eliminar_sede(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM equipo WHERE idsede=%s", (id,))
    count = cur.fetchone()[0]
    if count > 0:
        flash("❌ No se puede eliminar: existen equipos en esta sede.", "danger")
    else:
        cur.execute("DELETE FROM sede WHERE id=%s", (id,))
        conn.commit()
        flash("🗑️ Sede eliminada.", "warning")

    cur.close()
    conn.close()
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


# --------------------------
# CRUD OFICINA
# --------------------------
@invequip_bp.route('/ubicacion/oficina/nuevo', methods=['POST'])
def nueva_oficina():
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO oficina (oficina_salon) VALUES (%s)", (nombre,))
    conn.commit()
    cur.close()
    conn.close()
    flash("✅ Oficina creada con éxito.", "success")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/oficina/actualizar/<int:id>', methods=['POST'])
def actualizar_oficina(id):
    nombre = request.form['nombre']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE oficina SET oficina_salon=%s WHERE id=%s", (nombre, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("✏️ Oficina actualizada.", "info")
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))


@invequip_bp.route('/ubicacion/oficina/eliminar/<int:id>', methods=['POST'])
def eliminar_oficina(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM equipo WHERE idoficina=%s", (id,))
    count = cur.fetchone()[0]
    if count > 0:
        flash("❌ No se puede eliminar: existen equipos en esta oficina.", "danger")
    else:
        cur.execute("DELETE FROM oficina WHERE id=%s", (id,))
        conn.commit()
        flash("🗑️ Oficina eliminada.", "warning")

    cur.close()
    conn.close()
    return redirect(url_for('invequip.inventario_equipos', seccion='ubicacion'))
# ==============================
#       USUARIOS
# ==============================

@invequip_bp.route("/usuarios/baja/<int:id>", methods=["POST"])
def baja_usuario(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("CALL sp_baja_usuario(%s, %s, %s);", (id, descripcion, fecha_baja))
        conn.commit()
        flash(f"Usuario {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


@invequip_bp.route("/usuarios/revertir/<int:id>", methods=["POST"])
def revertir_baja_usuario(id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("CALL sp_revertir_baja_usuario(%s);", (id,))
        conn.commit()
        flash(f"Baja revertida para usuario {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


@invequip_bp.route("/usuarios/editar", methods=["POST"])
def editar_usuario():
    id = request.form.get("id")
    cc = request.form.get("cc")
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    idarea = request.form.get("idarea")
    idcargo = request.form.get("idcargo")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE usuario
            SET cc = %s, nombre = %s, email = %s, idarea = %s, idcargo = %s
            WHERE id = %s
        """, (cc, nombre, email, idarea, idcargo, id))
        conn.commit()
        flash(f"Usuario {id} actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos", seccion="usuarios"))




# ==============================
#       ÁREAS
# ==============================
@invequip_bp.route("/areas/crear", methods=["POST"])
def crear_area():
    area = request.form.get("area")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO area(area) VALUES (%s)", (area,))
        conn.commit()
        flash("Área creada correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


@invequip_bp.route("/areas/eliminar/<int:id>", methods=["POST"])
def eliminar_area(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM area WHERE id = %s", (id,))
        conn.commit()
        flash("Área eliminada correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


# ==============================
#       CARGOS
# ==============================
@invequip_bp.route("/cargos/crear", methods=["POST"])
def crear_cargo():
    descripcion = request.form.get("descripcion")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO cargo(descripcion) VALUES (%s)", (descripcion,))
        conn.commit()
        flash("Cargo creado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


@invequip_bp.route("/cargos/eliminar/<int:id>", methods=["POST"])
def eliminar_cargo(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cargo WHERE id = %s", (id,))
        conn.commit()
        flash("Cargo eliminado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


# ==============================
#       TELÉFONOS
# ==============================
@invequip_bp.route("/telefonos/crear", methods=["POST"])
def crear_telefono():
    numero = request.form.get("numero")
    idusuario = request.form.get("idusuario")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO telefono(numero, idusuario) VALUES (%s, %s)", (numero, idusuario))
        conn.commit()
        flash("Teléfono agregado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))



@invequip_bp.route("/telefonos/eliminar/<int:id>", methods=["POST"])
def eliminar_telefono(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM telefono WHERE id = %s", (id,))
        conn.commit()
        flash("Teléfono eliminado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))
# ==============================
#       ÁREAS - EDITAR
# ==============================
@invequip_bp.route("/areas/editar/<int:id>", methods=["POST"])
def editar_area(id):
    area = request.form.get("area")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE area SET area = %s WHERE id = %s", (area, id))
        conn.commit()
        flash("Área actualizada correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


# ==============================
#       CARGOS - EDITAR
# ==============================
@invequip_bp.route("/cargos/editar/<int:id>", methods=["POST"])
def editar_cargo(id):
    descripcion = request.form.get("descripcion")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE cargo SET descripcion = %s WHERE id = %s", (descripcion, id))
        conn.commit()
        flash("Cargo actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))


# ==============================
#       TELÉFONOS - EDITAR
# ==============================
@invequip_bp.route("/telefonos/editar/<int:id>", methods=["POST"])
def editar_telefono(id):
    numero = request.form.get("numero")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE telefono SET numero = %s WHERE id = %s", (numero, id))
        conn.commit()
        flash("Teléfono actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="usuarios"))

@invequip_bp.route("/usuarios/crear", methods=["POST"])
def crear_usuario():
    cc = request.form.get("cc")
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    idarea = request.form.get("idarea")
    idcargo = request.form.get("idcargo")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuario (cc, nombre, email, idarea, idcargo, baja)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (cc, nombre, email, idarea, idcargo))
        conn.commit()
        flash(f"Usuario {nombre} creado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos", seccion="usuarios"))
