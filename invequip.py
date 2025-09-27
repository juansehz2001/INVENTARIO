from flask import Blueprint, render_template, session, redirect, url_for, flash, request,jsonify
from conexion import get_connection
import psycopg2
from psycopg2 import sql
from datetime import date
import base64

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
               a.area, c.descripcion, t.numero,a.id,c.id
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
        WHERE b.tabla = 'almacenamiento'
        ORDER BY b.id DESC;
    """)
    bajas = cur.fetchall()
    cur.execute("""
        SELECT b.id, b.idregistro,b.tabla, b.descripcion, b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'board'
        ORDER BY b.id DESC;
    """)
    bajasboard = cur.fetchall()
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
       # === Consulta usuarios dominio ===
    cur.execute("SELECT id, nombre FROM usuariodominio ORDER BY id;")
    usuarios_dominio = cur.fetchall()
    # === Técnicos con teléfonos ===
    cur.execute("""
        SELECT t.id,
       t.cc_nit,
       t.nombre,
       t.fecharegistro,
       STRING_AGG(tt.numero, ', ') AS telefonos
FROM tecnicos t
LEFT JOIN teletec tt ON t.id = tt.idtecnicos
GROUP BY t.id, t.cc_nit, t.nombre, t.fecharegistro
ORDER BY t.id;
    """)
    tecnicos = cur.fetchall()

    # === Técnicos solos (para combos/modales) ===
    cur.execute("SELECT id, cc_nit, nombre FROM tecnicos ORDER BY id;")
    tecnicos_list = cur.fetchall()

    # === Teléfonos técnicos (por separado si quieres CRUD directo) ===
    cur.execute("""
        SELECT tt.id, tt.numero, t.id AS idtecnico, t.nombre
    FROM teletec tt
    LEFT JOIN tecnicos t ON t.id = tt.idtecnicos
    ORDER BY tt.id;
    """)
    teletec = cur.fetchall()
    # sistema operativo
    cur.execute("""
        select id,descripcion,arquitectura from sistemaopera order by id;
    """)
    sistemaoperas  = cur.fetchall()
     # sistema operativo
    cur.execute("""
         select id,marca,modelo,frecuencia,nucleos,plataforma,baja from procesador
         where baja = false order by id;
    """)
    procesador  = cur.fetchall()
    cur.execute("""
        SELECT b.id, b.idregistro,b.tabla, b.descripcion, b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'procesador'
        ORDER BY b.id DESC;
    """)
    bajasprocesador = cur.fetchall()
    cur.execute("""
         select id,tarjetamadre,chipset,baja from board
         where baja = false order by id;
    """)
    board  = cur.fetchall()
    cur.execute("""select gp.id,g.id,g.tipo,g.capacidad,g.marca,g.chipset from grafica g left join graficapc gp on gp.idgrafica=g.id where gp.baja=false order by gp.id;""")
    graficapc  = cur.fetchall()
    cur.execute("""select id,tipo,capacidad,marca,chipset from grafica order by id;""")
    grafica  = cur.fetchall()
    cur.execute("""
                 SELECT b.id, b.idregistro,b.tabla, b.descripcion, b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'graficapc'
        ORDER BY b.id DESC;
    """)
    graficabaja  = cur.fetchall()
    cur.execute("""
        SELECT l.id, l.nombresoftware, l.fechacompra, l.fechaexpiracion, 
               l.clavelicencia, l.idequipo, e.codigo
        FROM licenciasequipo l
        LEFT JOIN equipo e ON e.id = l.idequipo
        ORDER BY l.id DESC;
    """)
    licencias = cur.fetchall()
    cur.execute("""
        SELECT m.id, m.idequipo, e.codigo, m.fecharealizado, m.fechaincripcion,
               m.tipo, m.descripcion, t.nombre AS tecnico
        FROM mantenimientoobservacionesugerencias m
        LEFT JOIN equipo e ON e.id = m.idequipo
        LEFT JOIN tecnicos t ON t.id = m.idtecnico
        ORDER BY m.fecharealizado DESC;
    """)
    mantenimientos = cur.fetchall()
      # === Memorias ===
    cur.execute("""
        SELECT m.id, m.marca, m.idequipo, m.baja, 
               r.id AS idmemoriaram, r.tipo, r.capacidad, r.frecuencia
        FROM memoria m
        LEFT JOIN memoriaram r ON m.idmemoriaram = r.id
        WHERE m.baja = false
        ORDER BY m.id;
    """)
    memorias = cur.fetchall()

    cur.execute("SELECT id, tipo, capacidad, frecuencia FROM memoriaram ORDER BY id;")
    memoriasram = cur.fetchall()

    cur.execute("""
        SELECT b.id, b.idregistro, b.tabla, b.descripcion, 
               b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'memoria'
        ORDER BY b.id DESC;
    """)
    bajas_memoria = cur.fetchall()
    cur.execute("""
        SELECT p.id,mp.marca,p.pulgadas,p.voltaje,p.amperaje,p.serial,p.idequipo,p.baja,
               mp.id
        FROM pantalla p
        LEFT JOIN marcapantalla mp ON mp.id = p.idmarcapantalla
        WHERE p.baja = false
        ORDER BY p.id;
    """)
    pantalla = cur.fetchall()

    cur.execute("SELECT id, marca FROM marcapantalla ORDER BY id;")
    tipopantalla = cur.fetchall()

    cur.execute("""
        SELECT b.id, b.idregistro, b.tabla, b.descripcion, 
               b.fechabaja, b.fecharegistro
        FROM baja b
        WHERE b.tabla = 'pantalla'
        ORDER BY b.id DESC;
    """)
    bajas_pantalla = cur.fetchall()
    cur.execute("""
        SELECT p.id, m.marcas, p.modelo, p.serial, p.descripcion,
               e.codigo, p.idequipo
        FROM perisfericos p
        LEFT JOIN marcaperis m ON p.idmarca = m.id
        LEFT JOIN equipo e ON p.idequipo = e.id
        WHERE p.baja = FALSE
        ORDER BY p.id DESC
    """)
    perisfericos = cur.fetchall()

    # Traer marcas
    cur.execute("SELECT id, marcas FROM marcaperis ORDER BY marcas ASC")
    marcaperis = cur.fetchall()

    # Traer bajas
    cur.execute("""
        SELECT id, idregistro, tabla, descripcion, fechabaja, fecharegistro
        FROM baja
        WHERE tabla = 'perisfericos'
        ORDER BY fechabaja DESC
    """)
    bajas_perisfericos = cur.fetchall()

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
                           bajas_usuarios=bajas_usuarios,
                           usuarios_dominio=usuarios_dominio,
                           tecnicos=tecnicos,
                           tecnicos_list=tecnicos_list,
                           teletec=teletec,
                           sistemaoperas =sistemaoperas,
                           procesador =procesador,
                           bajasprocesador =bajasprocesador,
                           bajasboard =bajasboard,
                           grafica=grafica,
                           graficapc=graficapc,
                           graficabaja=graficabaja,
                           licencias=licencias,
                           board =board,
                           mantenimientos=mantenimientos,
                           memorias=memorias,
                           memoriasram=memoriasram,
                           bajas_memoria=bajas_memoria,
                           pantalla=pantalla,
                           tipopantalla=tipopantalla,
                           perisfericos=perisfericos,
                           marcaperis=marcaperis,
                           bajas_perisfericos=bajas_perisfericos,
                           bajas_pantalla=bajas_pantalla,
                           date=date)


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


# =========================
# CRUD USUARIOS DOMINIO
# =========================

@invequip_bp.route("/agregar_usuario_dominio", methods=["POST"])
def agregar_usuario_dominio():
    nombre = request.form.get("nombre")
    if not nombre:
        flash("El nombre es obligatorio", "danger")
        return redirect(url_for("invequip.inventario_equipos"))
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO usuariodominio (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Usuario de dominio agregado correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="usuariodominio"))


@invequip_bp.route("/editar_usuario_dominio", methods=["POST"])
def editar_usuario_dominio():
    id_ud = request.form.get("id")
    nombre = request.form.get("nombre")

    print("DEBUG >>> id:", id_ud, "nombre:", nombre)  # 👈 agrega esto

    if not id_ud or not nombre:
        flash("Datos incompletos", "danger")
        return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuariodominio SET nombre = %s WHERE id = %s", (nombre, id_ud))
    conn.commit()
    cur.close()
    conn.close()

    flash("Usuario de dominio actualizado correctamente", "warning")
    return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))


@invequip_bp.route("/eliminar_usuario_dominio", methods=["POST"])
def eliminar_usuario_dominio():
    id_ud = request.form.get("id")

    if not id_ud:
        flash("ID inválido", "danger")
        return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar si el usuario existe
        cur.execute("SELECT 1 FROM usuariodominio WHERE id = %s", (id_ud,))
        if not cur.fetchone():
            flash("El usuario de dominio no existe", "warning")
            return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))

        # Verificar si está referenciado en caracteristicasequipo
        cur.execute("SELECT COUNT(*) FROM caracteristicasequipo WHERE idusuariodominio = %s", (id_ud,))
        count = cur.fetchone()[0]
        if count > 0:
            flash("No se puede eliminar: el usuario está vinculado a características de equipo", "danger")
            return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))

        # Eliminar si no está referenciado
        cur.execute("DELETE FROM usuariodominio WHERE id = %s", (id_ud,))
        conn.commit()
        flash("Usuario de dominio eliminado correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos", seccion="usuariodominio"))

# ➕ Agregar Técnico
@invequip_bp.route("/agregar_tecnico", methods=["POST"])
def agregar_tecnico():
    cc_nit = request.form["cc_nit"]
    nombre = request.form["nombre"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tecnicos (cc_nit, nombre) VALUES (%s, %s)", (cc_nit, nombre))
    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Técnico agregado correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="tecnicos"))


# ✏️ Editar Técnico
@invequip_bp.route("/editar_tecnico", methods=["POST"])
def editar_tecnico():
    id_tecnico = request.form["id"]
    cc_nit = request.form["cc_nit"]
    nombre = request.form["nombre"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tecnicos SET cc_nit=%s, nombre=%s WHERE id=%s", (cc_nit, nombre, id_tecnico))
    conn.commit()
    cur.close()
    conn.close()

    flash("✏️ Técnico actualizado correctamente", "warning")
    return redirect(url_for("invequip.inventario_equipos",seccion="tecnicos"))


# 🗑️ Eliminar Técnico
@invequip_bp.route("/eliminar_tecnico", methods=["POST"])
def eliminar_tecnico():
    id_tecnico = request.form["id"]

    conn = get_connection()
    cur = conn.cursor()

    # 🔎 Verificar si el técnico está en mantenimientos
    cur.execute("SELECT 1 FROM mantenimientoobservacionesugerencias WHERE idtecnico = %s LIMIT 1", (id_tecnico,))
    existe = cur.fetchone()

    if existe:
        cur.close()
        conn.close()
        flash("⚠️ No se puede eliminar: el técnico está asignado a mantenimientos.", "warning")
        return redirect(url_for("invequip.inventario_equipos", seccion="tecnicos"))

    # 🗑️ Si no tiene mantenimientos, borramos dependencias
    cur.execute("DELETE FROM teletec WHERE idtecnicos = %s", (id_tecnico,))
    cur.execute("DELETE FROM tecnicos WHERE id = %s", (id_tecnico,))
    conn.commit()
    cur.close()
    conn.close()

    flash("🗑️ Técnico eliminado correctamente", "danger")
    return redirect(url_for("invequip.inventario_equipos", seccion="tecnicos"))

# ➕ Agregar Teléfono Técnico
@invequip_bp.route("/agregar_telefono_tecnico", methods=["POST"])
def agregar_telefono_tecnico():
    idtecnico = request.form["idtecnico"]
    numero = request.form["numero"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO teletec (idtecnicos, numero) VALUES (%s, %s)", (idtecnico, numero))
    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Teléfono de técnico agregado correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="tecnicos"))


@invequip_bp.route("/editar_telefono_tecnico", methods=["POST"])
def editar_telefono_tecnico():
    id_tel = request.form["id"]
    numero = request.form["numero"]
    idtecnico = request.form["idtecnico"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE teletec SET numero=%s, idtecnicos=%s WHERE id=%s",
                (numero, idtecnico, id_tel))
    conn.commit()
    cur.close()
    conn.close()

    flash("✏️ Teléfono de técnico actualizado correctamente", "warning")
    return redirect(url_for("invequip.inventario_equipos", seccion="tecnicos"))



# 🗑️ Eliminar Teléfono Técnico
@invequip_bp.route("/eliminar_telefono_tecnico", methods=["POST"])
def eliminar_telefono_tecnico():
    id_tel = request.form["id"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM teletec WHERE id = %s", (id_tel,))
    conn.commit()
    cur.close()
    conn.close()

    flash("🗑️ Teléfono de técnico eliminado correctamente", "danger")
    return redirect(url_for("invequip.inventario_equipos",seccion="tecnicos"))

@invequip_bp.route("/agregar_so", methods=["POST"])
def agregar_so():
    descripcion = request.form["descripcion"]
    arquitectura = request.form["arquitectura"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sistemaopera (descripcion, arquitectura) VALUES (%s, %s)",
                (descripcion, arquitectura))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("invequip.inventario_equipos", seccion="so"))


@invequip_bp.route("/editar_so", methods=["POST"])
def editar_so():
    id_so = request.form["id"]
    descripcion = request.form["descripcion"]
    arquitectura = request.form["arquitectura"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE sistemaopera SET descripcion=%s, arquitectura=%s WHERE id=%s",
                (descripcion, arquitectura, id_so))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("invequip.inventario_equipos", seccion="so"))


@invequip_bp.route("/eliminar_so", methods=["POST"])
def eliminar_so():
    id_so = request.form.get("id")

    if not id_so:
        flash("ID inválido", "danger")
        return redirect(url_for("invequip.inventario_equipos", seccion="so"))

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar si el sistema operativo existe
        cur.execute("SELECT 1 FROM sistemaopera WHERE id = %s", (id_so,))
        if not cur.fetchone():
            flash("El sistema operativo no existe", "warning")
            return redirect(url_for("invequip.inventario_equipos", seccion="so"))

        # Verificar si está referenciado en caracteristicasequipo
        cur.execute("SELECT COUNT(*) FROM caracteristicasequipo WHERE idsistemaoperativo = %s", (id_so,))
        count = cur.fetchone()[0]
        if count > 0:
            flash("No se puede eliminar: el sistema operativo está vinculado a características de equipo", "danger")
            return redirect(url_for("invequip.inventario_equipos", seccion="so"))

        # Eliminar si no está referenciado
        cur.execute("DELETE FROM sistemaopera WHERE id = %s", (id_so,))
        conn.commit()
        flash("Sistema operativo eliminado correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos", seccion="so"))
# ======================
# CRUD PROCESADOR
# ======================

@invequip_bp.route("/agregar_procesador", methods=["POST"])
def agregar_procesador():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))

    marca = request.form["marca"]
    modelo = request.form["modelo"]
    frecuencia = request.form["frecuencia"]
    nucleos = request.form["nucleos"]
    plataforma = request.form["plataforma"]

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO procesador (marca, modelo, frecuencia, nucleos, plataforma)
            VALUES (%s, %s, %s, %s, %s)
        """, (marca, modelo, frecuencia, nucleos, plataforma))
        conn.commit()
        flash("Procesador agregado exitosamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al agregar procesador: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="procesador"))


@invequip_bp.route("/editar_procesador", methods=["POST"])
def editar_procesador():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))

    id_proc = request.form["id"]
    marca = request.form["marca"]
    modelo = request.form["modelo"]
    frecuencia = request.form["frecuencia"]
    nucleos = request.form["nucleos"]
    plataforma = request.form["plataforma"]

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE procesador
            SET marca = %s, modelo = %s, frecuencia = %s, nucleos = %s, plataforma = %s
            WHERE id = %s
        """, (marca, modelo, frecuencia, nucleos, plataforma, id_proc))
        conn.commit()
        flash("Procesador actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al editar procesador: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="procesador"))

@invequip_bp.route("/baja_procesador/<int:id>", methods=["POST"])
def baja_procesador(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_baja_procesador(%s, %s, %s)", (id, descripcion, fecha_baja))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="procesador"))

@invequip_bp.route("/revertir_baja_procesador/<int:id>", methods=["POST"])
def revertir_baja_procesador(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_revertir_baja_procesador(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="procesador"))


# ======================
# CRUD BOARD
# ======================

@invequip_bp.route("/agregar_board", methods=["POST"])
def agregar_board():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))

    tarjetamadre = request.form["tarjetamadre"]
    chipset = request.form["chipset"]


    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO board (tarjetamadre, chipset)
            VALUES (%s, %s)
        """, (tarjetamadre, chipset))
        conn.commit()
        flash("board agregado exitosamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al agregar board: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="board"))


@invequip_bp.route("/editar_board", methods=["POST"])
def editar_board():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))

    id_board = request.form["id"]
    tarjetamadre = request.form["tarjetamadre"]
    chipset = request.form["chipset"]

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE board
            SET tarjetamadre = %s, chipset = %s
            WHERE id = %s
        """, (tarjetamadre, chipset, id_board))
        conn.commit()
        flash("board actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al editar board: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="board"))

@invequip_bp.route("/baja_board/<int:id>", methods=["POST"])
def baja_board(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_baja_board(%s, %s, %s)", (id, descripcion, fecha_baja))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="board"))

@invequip_bp.route("/revertir_baja_board/<int:id>", methods=["POST"])
def revertir_baja_board(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_revertir_baja_board(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="board"))


# ==============================
#   API EQUIPOS (FUNCIONALES / BAJA)
# ==============================
@invequip_bp.route("/api/equipos")
def api_equipos():
    if "usuario" not in session:
        return jsonify({"error": "No autorizado"}), 401

    estado = request.args.get("estado", "funcionales")
    search = request.args.get("search", "").strip().lower()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 2))

    if per_page not in [2, 4, 8, 16, 32, 64]:
        per_page = 2

    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()

    base_query = """
        SELECT eq.id, eq.codigo, eq.tipo, eq.marca, eq.modelo, eq.serial,
               eq.fechacompra, eq.estado, eq.foto, eq.fecharegistro,
               s.sede, o.oficina_salon, p.piso, u.nombre
        FROM equipo eq
        LEFT JOIN sede s ON s.id = eq.idsede
        LEFT JOIN oficina o ON o.id = eq.idoficina
        LEFT JOIN piso p ON p.id = eq.idpiso
        LEFT JOIN usuario u ON u.id = eq.idusuario
        WHERE eq.baja = %s
    """

    params = [False if estado == "funcionales" else True]

    if search:
        base_query += """ 
            AND (LOWER(eq.codigo) LIKE %s OR LOWER(eq.tipo) LIKE %s OR LOWER(eq.marca) LIKE %s 
                 OR LOWER(eq.modelo) LIKE %s OR LOWER(eq.serial) LIKE %s 
                 OR LOWER(s.sede) LIKE %s OR LOWER(o.oficina_salon) LIKE %s
                 OR LOWER(p.piso) LIKE %s OR LOWER(u.nombre) LIKE %s)
        """
        like_search = f"%{search}%"
        params.extend([like_search] * 9)

    count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subq"
    cur.execute(count_query, tuple(params))
    total = cur.fetchone()[0]

    base_query += " ORDER BY eq.id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    equipos = []
    for r in rows:
        foto_base64 = None
        if r[8]:
            foto_base64 = base64.b64encode(r[8]).decode("utf-8")

        equipos.append({
            "id": r[0],
            "codigo": r[1],
            "tipo": r[2],
            "marca": r[3],
            "modelo": r[4],
            "serial": r[5],
            "fechacompra": r[6].strftime("%Y-%m-%d") if r[6] else None,
            "estado": r[7],
            "foto": foto_base64, 
            "fecharegistro": r[9].strftime("%Y-%m-%d %H:%M:%S") if r[9] else None,
            "sede": r[10]if r[10] else "No asignado",
            "oficina": r[11]if r[11] else "No asignado",
            "piso": r[12]if r[12] else "No asignado",
            "usuario": r[13]if r[13] else "No asignado"
        })

    return jsonify({
        "equipos": equipos,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total // per_page) + (1 if total % per_page else 0)
    })
@invequip_bp.route("/agregar_equipo", methods=["POST"])
def agregar_equipo():
    if "usuario" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("home"))

    data = request.form
    foto = request.files.get("foto")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # === 1. Insert en equipo ===
        cur.execute("""
            INSERT INTO equipo (
                codigo, tipo, marca, modelo, serial, fechacompra, estado, 
                idsede, idoficina, idpiso, idusuario, foto
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            data.get("codigo"),
            data.get("tipo"),
            data.get("marca"),
            data.get("modelo"),
            data.get("serial"),
            data.get("fechacompra") or None,
            data.get("estado"),
            data.get("idsede"),
            data.get("idoficina"),
            data.get("idpiso"),
            data.get("idusuario") or None,
            psycopg2.Binary(foto.read()) if foto else None
        ))
        id_equipo = cur.fetchone()[0]

        # === 2. Insert en caracteristicasequipo ===
        cur.execute("""
            INSERT INTO caracteristicasequipo (
                idequipo, direccionmac, ip, observaciones, nombreequipo, sockets, frecuenciaram, 
                idusuariodominio, anidesk, idboard, idsistemaoperativo, idprocesador
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            id_equipo,
            data.get("direccionmac"),
            data.get("ip"),
            data.get("observaciones"),
            data.get("nombreequipo"),
            data.get("sockets") or None,
            data.get("frecuenciaram") or None,
            data.get("idusuariodominio") or None,
            data.get("anidesk"),
            data.get("idboard") or None,
            data.get("idsistemaoperativo") or None,
            data.get("idprocesador") or None
        ))

        conn.commit()
        flash("✅ Equipo agregado correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al agregar equipo: {str(e)}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos"))

@invequip_bp.route("/api/revertir_baja/<int:id>", methods=["POST"])
def revertir_baja(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL sp_revertir_baja_equipo(%s)", (id,))
            conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    

# Ejecutar grafica_baja
@invequip_bp.route("/grafica/baja/<int:id>", methods=["POST"])
def baja_grafica(id):
    fecha_baja = request.form.get("fecha_baja")
    descripcion = request.form.get("descripcion")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL registrar_baja_grafica(%s, %s, %s)", (id, fecha_baja, descripcion))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="grafica"))


# Ejecutar sp_revertir_baja_grafica
@invequip_bp.route("/grafica/revertir/<int:id>", methods=["POST"])
def revertir_baja_grafica(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL revertir_baja_grafica(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="grafica"))
# =========================
# NUEVA grafica
# =========================
@invequip_bp.route("/grafica/nueva_grafica", methods=["POST"])
def nueva_grafica():
    capacidad = request.form.get("capacidad")
    tipo = request.form.get("tipo")
    marca = request.form.get("marca")
    chipset = request.form.get("chipset")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("insert into grafica (tipo,capacidad,marca,chipset) values (%s,%s,%s,%s)", (tipo,capacidad,marca,chipset))
        conn.commit()
        flash("grafica registrada correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar grafica: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="grafica"))


# =========================
# NUEVO ALMACENAMIENTO
# =========================
@invequip_bp.route("/graficapc/nuevo", methods=["POST"])
def nuevo_graficapc():
    id_grafica = request.form.get("id_grafica")
    id_equipo = None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "insert into graficapc (idgrafica,idequipo) values (%s, %s)",
            (id_grafica, id_equipo),
        )
        conn.commit()
        flash("graficapc registrado correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar graficapc: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="grafica"))
# =========================
# ACTUALIZAR ALMACENAMIENTO
# =========================
@invequip_bp.route("/grafica/actualizar/<int:id>", methods=["POST"])
def actualizar_grafica(id):
    id_graficapc = request.form.get("id_graficapc")or None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE graficapc 
            SET idgrafica = %s
            WHERE id = %s
        """, (id_graficapc, id))
        conn.commit()
        flash(f"Registro {id} actualizado correctamente ✅", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="grafica"))
@invequip_bp.route("/licencias/agregar", methods=["POST"])
def agregar_licencia():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO licenciasequipo (nombresoftware, fechacompra, fechaexpiracion, clavelicencia, idequipo)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        request.form["nombresoftware"],
        request.form["fechacompra"],
        request.form["fechaexpiracion"],
        request.form["clavelicencia"],
        request.form.get("idequipo") if request.form.get("idequipo") else None
    ))
    conn.commit()
    cur.close()
    conn.close()
    flash("Licencia agregada correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="licencias"))

@invequip_bp.route("/licencias/editar/<int:id>", methods=["POST"])
def editar_licencia(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE licenciasequipo
        SET nombresoftware=%s, fechacompra=%s, fechaexpiracion=%s, clavelicencia=%s, idequipo=%s
        WHERE id=%s
    """, (
        request.form["nombresoftware"],
        request.form["fechacompra"],
        request.form["fechaexpiracion"],
        request.form["clavelicencia"],
        request.form.get("idequipo") if request.form.get("idequipo") else None,
        id
    ))
    conn.commit()
    cur.close()
    conn.close()
    flash("Licencia actualizada correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="licencias"))

@invequip_bp.route("/licencias/eliminar/<int:id>", methods=["POST"])
def eliminar_licencia(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM licenciasequipo WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Licencia eliminada correctamente", "danger")
    return redirect(url_for("invequip.inventario_equipos",seccion="licencias"))

@invequip_bp.route("/mantenimientos/add", methods=["POST"])
def add_mantenimiento():
    data = request.json
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mantenimientoobservacionesugerencias
            (idequipo, fecharealizado, fechaincripcion, tipo, descripcion, idtecnico)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data.get("idequipo"),
        data.get("fecharealizado"),
        data.get("fechaincripcion"),
        data.get("tipo"),
        data.get("descripcion"),
        data.get("idtecnico"),
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="mantenimientos"))
@invequip_bp.route("/mantenimientos/update/<int:id>", methods=["PUT"])
def update_mantenimiento(id):
    data = request.json
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE mantenimientoobservacionesugerencias
        SET idequipo=%s, fecharealizado=%s, fechaincripcion=%s,
            tipo=%s, descripcion=%s, idtecnico=%s
        WHERE id=%s
    """, (
        data.get("idequipo"),
        data.get("fecharealizado"),
        data.get("fechaincripcion"),
        data.get("tipo"),
        data.get("descripcion"),
        data.get("idtecnico"),
        id
    ))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="mantenimientos"))
@invequip_bp.route("/mantenimientos/delete/<int:id>", methods=["DELETE"])
def delete_mantenimiento(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mantenimientoobservacionesugerencias WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("invequip.inventario_equipos",seccion="mantenimientos"))
# === Crear memoria ===
@invequip_bp.route("/memoria/agregar", methods=["POST"])
def agregar_memoria():
    marca = request.form["marca"]
    idmemoriaram = request.form["idmemoriaram"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memoria (marca, idmemoriaram, idequipo) 
        VALUES (%s, %s, NULL)
    """, (marca, idmemoriaram))
    conn.commit()
    cur.close()
    conn.close()
    flash("Memoria agregada con éxito", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))


# === Editar memoria ===
@invequip_bp.route("/memoria/editar/<int:id>", methods=["POST"])
def editar_memoria(id):
    idmemoriaram = request.form["idmemoriaram"]
    marca = request.form["marca"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE memoria 
        SET idmemoriaram=%s, marca=%s
        WHERE id=%s
    """, (idmemoriaram, marca, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("Memoria editada con éxito", "info")
    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))


# === Eliminar memoria ===
@invequip_bp.route("/memoria/eliminar/<int:id>", methods=["POST"])
def eliminar_memoria(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM memoria WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Memoria eliminada con éxito", "danger")
    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))

# ----- RUTAS CRUD PARA memoriaram -----
@invequip_bp.route("/memoriaram/agregar", methods=["POST"])
def agregar_memoriaram():
    tipo = request.form.get("tipo", "").strip()
    capacidad = request.form.get("capacidad", "0").strip()
    frecuencia = request.form.get("frecuencia", "0").strip()

    try:
        capacidad = int(capacidad)
        frecuencia = int(frecuencia)
    except ValueError:
        flash("Capacidad y frecuencia deben ser números enteros.", "warning")
        return redirect(url_for("invequip.inventario_equipos"))

    if not tipo:
        flash("Debe indicar el tipo de memoria RAM.", "warning")
        return redirect(url_for("invequip.inventario_equipos",seccion="ram"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO memoriaram (tipo, capacidad, frecuencia) VALUES (%s, %s, %s)",
            (tipo, capacidad, frecuencia),
        )
        conn.commit()
        flash("Tipo de memoria RAM agregado.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al agregar memoriaram: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))


@invequip_bp.route("/memoriaram/editar/<int:id>", methods=["POST"])
def editar_memoriaram(id):
    tipo = request.form.get("tipo", "").strip()
    capacidad = request.form.get("capacidad", "0").strip()
    frecuencia = request.form.get("frecuencia", "0").strip()

    try:
        capacidad = int(capacidad)
        frecuencia = int(frecuencia)
    except ValueError:
        flash("Capacidad y frecuencia deben ser números enteros.", "warning")
        return redirect(url_for("invequip.inventario_equipos",seccion="ram"))

    if not tipo:
        flash("Debe indicar el tipo de memoria RAM.", "warning")
        return redirect(url_for("invequip.inventario_equipos"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE memoriaram SET tipo=%s, capacidad=%s, frecuencia=%s WHERE id=%s",
            (tipo, capacidad, frecuencia, id),
        )
        conn.commit()
        flash("Tipo de memoria RAM actualizado.", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error al editar memoriaram: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))


@invequip_bp.route("/memoriaram/eliminar/<int:id>", methods=["POST"])
def eliminar_memoriaram(id):
    """
    Estrategia: poner a NULL las referencias en 'memoria' y luego eliminar el registro de memoriaram.
    Evita errores por FK y deja los equipos/memorias sin referencia si corresponde.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1) Quitar referencias para evitar FK
        cur.execute("UPDATE memoria SET idmemoriaram = NULL WHERE idmemoriaram = %s", (id,))
        # 2) Eliminar el tipo
        cur.execute("DELETE FROM memoriaram WHERE id = %s", (id,))
        conn.commit()
        flash("Tipo de memoria RAM eliminado. Referencias en 'memoria' puestas a NULL.", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar memoriaram: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))

@invequip_bp.route("/memoriaram/baja/<int:id>", methods=["POST"])
def baja_memoriaram(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL registrar_baja_memoria(%s, %s, %s)", (id , fecha_baja, descripcion))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))

# Ejecutar sp_revertir_baja_almacenamiento
@invequip_bp.route("/memoriaram/revertir/<int:id>", methods=["POST"])
def revertir_baja_memoriaram(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL revertir_baja_memoria(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="ram"))


@invequip_bp.route("/pantalla/agregar", methods=["POST"])
def agregar_pantalla():
    idpantalla = request.form["idpantalla"]
    pulgadas = request.form["pulgadas"]
    voltaje = request.form["voltaje"]
    amperaje = request.form["amperaje"]
    serial = request.form["serial"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pantalla (idmarcapantalla,pulgadas,voltaje,amperaje,serial, idequipo) 
        VALUES (%s, %s,%s, %s,%s, NULL)
    """, (idpantalla,pulgadas,voltaje,amperaje,serial))
    conn.commit()
    cur.close()
    conn.close()
    flash("pantalla agregada con éxito", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))


# === Editar memoria ===
@invequip_bp.route("/pantalla/editar/<int:id>", methods=["POST"])
def editar_pantalla(id):
    idpantalla = request.form["idpantalla"]
    pulgadas = request.form["pulgadas"]
    voltaje = request.form["voltaje"]
    amperaje = request.form["amperaje"]
    serial = request.form["serial"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pantalla 
        SET idmarcapantalla=%s, pulgadas=%s,voltaje=%s,amperaje=%s,serial=%s
        WHERE id=%s
    """, (idpantalla,pulgadas,voltaje,amperaje,serial, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("pantalla editada con éxito", "info")
    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))

# ----- RUTAS CRUD PARA memoriaram -----
@invequip_bp.route("/tipopantalla/agregar", methods=["POST"])
def agregar_tipopantalla():
    marca = request.form.get("marca", "").strip()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO marcapantalla  (marca) VALUES (%s)",
            (marca,),
        )
        conn.commit()
        flash("Tipo de pantalla agregado.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al agregar Tipo de pantalla: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))


@invequip_bp.route("/tipopantalla/editar/<int:id>", methods=["POST"])
def editar_tipopantalla(id):
    marca = request.form.get("marca", "").strip()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE marcapantalla SET marca=%s WHERE id=%s",
            (marca, id),
        )
        conn.commit()
        flash("Tipo de pantalla RAM actualizado.", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error al editar Tipo de pantalla: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))


@invequip_bp.route("/tipopantalla/eliminar/<int:id>", methods=["POST"])
def eliminar_tipopantalla(id):

    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1) Quitar referencias para evitar FK
        cur.execute("UPDATE pantalla SET idmarcapantalla = NULL WHERE idmarcapantalla = %s", (id,))
        # 2) Eliminar el tipo
        cur.execute("DELETE FROM marcapantalla WHERE id = %s", (id,))
        conn.commit()
        flash("Tipo de marca pantalla eliminado. Referencias en 'pantalla' puestas a NULL.", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar pantalla: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))

@invequip_bp.route("/pantalla/baja/<int:id>", methods=["POST"])
def baja_pantalla(id):
    descripcion = request.form.get("descripcion")
    fecha_baja = request.form.get("fecha_baja")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL registrar_baja_pantalla(%s, %s, %s)", (id , fecha_baja, descripcion))
        conn.commit()
        flash(f"Registro {id} dado de baja correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))

# Ejecutar sp_revertir_baja_almacenamiento
@invequip_bp.route("/pantalla/revertir/<int:id>", methods=["POST"])
def revertir_baja_pantalla(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL revertir_baja_pantalla(%s)", (id,))
        conn.commit()
        flash(f"Baja revertida para {id}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("invequip.inventario_equipos",seccion="pantalla"))
@invequip_bp.route("/perisfericos/agregar", methods=["POST"])
def agregar_perisferico():
    modelo = request.form["modelo"]
    serial = request.form["serial"]
    descripcion = request.form["descripcion"]
    idmarca = request.form["idmarca"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO perisfericos (modelo, serial, descripcion, idmarca)
        VALUES (%s, %s, %s, %s)
    """, (modelo, serial, descripcion, idmarca))
    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Periférico agregado con éxito", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 EDITAR PERIFERICO
# =========================
@invequip_bp.route("/perisfericos/editar/<int:id>", methods=["POST"])
def editar_perisferico(id):
    modelo = request.form["modelo"]
    serial = request.form["serial"]
    descripcion = request.form["descripcion"]
    idmarca = request.form["idmarca"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE perisfericos
        SET modelo=%s, serial=%s, descripcion=%s, idmarca=%s
        WHERE id=%s
    """, (modelo, serial, descripcion, idmarca, id))
    conn.commit()
    cur.close()
    conn.close()

    flash("✏️ Periférico actualizado correctamente", "info")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 DAR DE BAJA PERIFERICO
# =========================
@invequip_bp.route("/perisfericos/baja/<int:id>", methods=["POST"])
def baja_perisferico(id):
    descripcion = request.form["descripcion"]
    fecha_baja = request.form["fecha_baja"]

    conn = get_connection()
    cur = conn.cursor()

    # Marcar como baja en perisfericos
    cur.execute("UPDATE perisfericos SET baja = TRUE WHERE id = %s", (id,))

    # Registrar en tabla bajas
    cur.execute("""
        INSERT INTO baja (idregistro, tabla, descripcion, fechabaja, fecharegistro)
        VALUES (%s, %s, %s, %s, %s)
    """, (id, "perisfericos", descripcion, fecha_baja, date.today()))

    conn.commit()
    cur.close()
    conn.close()

    flash("📉 Periférico dado de baja", "warning")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 REVERTIR BAJA
# =========================
@invequip_bp.route("/perisfericos/revertir_baja/<int:id>", methods=["POST"])
def revertir_baja_perisferico(id):
    conn = get_connection()
    cur = conn.cursor()

    # Restaurar registro
    cur.execute("UPDATE perisfericos SET baja = FALSE WHERE id = %s", (id,))
    # Eliminar de la tabla bajas
    cur.execute("DELETE FROM baja WHERE idregistro = %s AND tabla = 'perisfericos'", (id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("🔄 Baja revertida correctamente", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 AGREGAR MARCA
# =========================
@invequip_bp.route("/marcaperis/agregar", methods=["POST"])
def agregar_marcaperis():
    marcas = request.form["marcas"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO marcaperis (marcas) VALUES (%s)", (marcas,))
    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Marca agregada", "success")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 EDITAR MARCA
# =========================
@invequip_bp.route("/marcaperis/editar/<int:id>", methods=["POST"])
def editar_marcaperis(id):
    marcas = request.form["marcas"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE marcaperis SET marcas=%s WHERE id=%s", (marcas, id))
    conn.commit()
    cur.close()
    conn.close()

    flash("✏️ Marca actualizada", "info")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))


# =========================
# 📌 ELIMINAR MARCA
# =========================
@invequip_bp.route("/marcaperis/eliminar/<int:id>", methods=["POST"])
def eliminar_marcaperis(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM marcaperis WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("🗑️ Marca eliminada", "danger")
    return redirect(url_for("invequip.inventario_equipos",seccion="perisfericos"))
