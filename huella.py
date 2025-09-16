from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from conexion import get_connection
import psycopg2.extras
import base64
import cbor2
import struct

huella_bp = Blueprint("huella", __name__, template_folder="templates")


def parse_attestation(attestation_b64):
    """Recibe el attestationObject en base64, devuelve (credential_id, public_key_cose, sign_count)."""
    attestation_bytes = base64.b64decode(attestation_b64)
    attestation = cbor2.loads(attestation_bytes)

    auth_data = attestation.get("authData")
    if not auth_data:
        raise ValueError("authData no encontrado en attestationObject")

    # Estructura de authData:
    # rpIdHash (32) + flags (1) + signCount (4) + attestedCredentialData (variable)
    rp_id_hash = auth_data[:32]
    flags = auth_data[32]
    sign_count = struct.unpack(">I", auth_data[33:37])[0]

    # Extraer credentialIdLength (2 bytes)
    cred_id_len = struct.unpack(">H", auth_data[53:55])[0]
    credential_id = auth_data[55:55 + cred_id_len]

    # Lo que queda después del credentialId es la COSE_Key
    cose_key = cbor2.loads(auth_data[55 + cred_id_len:])

    return credential_id, cose_key, sign_count


@huella_bp.route("/registrar_huella", methods=["GET", "POST"])
def registrar_huella():
    if "usuario" not in session:
        flash("Debes iniciar sesión antes de registrar tu huella.", "warning")
        return redirect(url_for("login"))

    usuario = session["usuario"]
    ya_registrada = False

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Validar si ya existe credential_id registrado
        cur.execute("SELECT credential_id FROM users WHERE username = %s", (usuario,))
        existente = cur.fetchone()

        if existente and existente["credential_id"]:
            ya_registrada = True
            flash("⚠ Ya tienes una huella registrada. No es posible registrar otra.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("home"))

    except Exception as e:
        flash("Error al verificar credencial: " + str(e), "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        credential_encoded = request.form.get("credential_id")
        attestation_encoded = request.form.get("attestationObject")  # ahora viene bien nombrado

        if not credential_encoded or not attestation_encoded:
            flash("❌ No se recibió información de la huella. Intenta nuevamente.", "danger")
            return redirect(url_for("huella.registrar_huella"))

        try:
            # ✅ Parsear attestation
            credential_id, public_key_cose, sign_count = parse_attestation(attestation_encoded)

            conn = get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute("""
                UPDATE users 
                SET credential_id = %s, public_key = %s, sign_count = %s
                WHERE username = %s
            """, (
                credential_id,                 # BYTEA
                cbor2.dumps(public_key_cose),  # serializamos COSE_Key
                sign_count,
                usuario
            ))

            conn.commit()
            flash("✅ Huella registrada correctamente.", "success")
            return redirect(url_for("home"))

        except Exception as e:
            flash("Error al registrar credencial: " + str(e), "danger")

        finally:
            cur.close()
            conn.close()
    else:
        # GET → solo cerramos conexión
        cur.close()
        conn.close()

    return render_template("registrar_huella.html", usuario=usuario, ya_registrada=ya_registrada)
