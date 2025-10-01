from flask import Blueprint, render_template

ubicacion = Blueprint("ubicacion", __name__, template_folder="templates")

@ubicacion.route("/ubicacion_eds")
def ubicacion_eds():
    # 🔹 Ubicaciones en Villavicencio
    ubicaciones = [
        {
            "nombre": "Administrativa EDS Pavitos",
            "lat": 4.147054441284038,
            "lng": -73.61043267617984,
            "descripcion": "Estación Administrativa Pavitos"
        },
        {
            "nombre": "EDS Catama",
            "lat": 4.146098816960341,
            "lng": -73.61406272537714,
            "descripcion": "Estación de Servicio Catama"
        },
        {
            "nombre": "EDS Cusiana y EDS Terminal",
            "lat": 4.131403864603484,
            "lng": -73.60507684564601,
            "descripcion": "Estación de Servicio Cusiana y Terminal"
        },
        {
            "nombre": "Señora Villavicencio",
            "lat": 4.13004835264163,
            "lng": -73.60617201518829,
            "descripcion": "Estación Señora Villavicencio"
        },
        {
            "nombre": "EDS Gasollano",
            "lat": 4.123066612229535,
            "lng": -73.61277162081247,
            "descripcion": "Estación de Servicio Gasollano"
        },
        {
            "nombre": "EDS Pasoganadero",
            "lat": 4.116825015044814,
            "lng": -73.58969137069018,
            "descripcion": "Estación de Servicio Pasoganadero"
        },
        {
            "nombre": "Esperanza EDS",
            "lat": 4.132390887574401,
            "lng": -73.63162364734681,
            "descripcion": "Estación de Servicio Esperanza"
        },
        {
            "nombre": "EDS Primavera",
            "lat": 4.12627075471155,
            "lng": -73.62018242260748,
            "descripcion": "Estación de Servicio Primavera"
        }
    ]
    return render_template("ubicacion_eds.html", ubicaciones=ubicaciones)

