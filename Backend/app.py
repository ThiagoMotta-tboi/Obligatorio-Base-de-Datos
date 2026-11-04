from datetime import date, timedelta
from decimal import Decimal

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from mysql.connector import Error as MySQLError

from config import JWT_SECRET_KEY
from db import query
from routes import (auth_routes, complejos, equipos, facultades, jugadores, partidos,
                    planillas, reportes, sanciones, torneos, turnos)
from utils import ErrorNegocio


class ProveedorJSON(DefaultJSONProvider):
    """Convierte los tipos que devuelve MySQL a valores JSON legibles."""

    def default(self, o):
        if isinstance(o, date):  # también cubre datetime
            return o.isoformat()
        if isinstance(o, timedelta):  # las columnas TIME llegan como timedelta
            segundos = int(o.total_seconds())
            return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}"
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


# Errores de MySQL más comunes, traducidos para el usuario
MENSAJES_MYSQL = {
    1048: ("Falta un campo obligatorio", 400),
    1062: ("Ya existe un registro con esos datos", 409),
    1265: ("Valor inválido para alguno de los campos", 400),
    1451: ("No se puede eliminar o modificar: hay registros que dependen de este", 409),
    1452: ("Alguno de los datos relacionados no existe", 400),
    3819: ("Los datos no cumplen una restricción de la base", 400),
}

app = Flask(__name__)
app.json_provider_class = ProveedorJSON
app.json = ProveedorJSON(app)
app.json.sort_keys = False
app.json.ensure_ascii = False
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)  # una jornada de trabajo

CORS(app)
JWTManager(app)

for modulo in (auth_routes, facultades, jugadores, torneos, complejos, turnos,
               equipos, partidos, planillas, sanciones, reportes):
    app.register_blueprint(modulo.bp)


@app.errorhandler(ErrorNegocio)
def error_negocio(e):
    return jsonify(error=e.mensaje), e.status


@app.errorhandler(MySQLError)
def error_mysql(e):
    if e.errno in MENSAJES_MYSQL:
        mensaje, status = MENSAJES_MYSQL[e.errno]
        return jsonify(error=mensaje, detalle=e.msg), status
    if e.errno in (2003, 2005, 1045, 1049):
        return jsonify(error="No se pudo conectar a la base de datos", detalle=e.msg), 503
    return jsonify(error="Error en la base de datos", detalle=e.msg), 500


@app.get("/api/salud")
def salud():
    query("SELECT 1")
    return jsonify(estado="ok")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
