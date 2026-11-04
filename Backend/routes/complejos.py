from flask import Blueprint, jsonify

from auth import cualquier_rol, solo_admin
from db import execute, query
from utils import ErrorNegocio, booleano, datos_json, opcion, requeridos

bp = Blueprint("complejos", __name__, url_prefix="/api")

SUPERFICIES = ("sintetico", "parquet")


def _buscar_complejo(id_complejo):
    complejo = query("SELECT * FROM complejo WHERE id_complejo = %s", (id_complejo,), one=True)
    if not complejo:
        raise ErrorNegocio("Complejo no encontrado", 404)
    return complejo


def _buscar_cancha(id_complejo, nombre_cancha):
    cancha = query("SELECT * FROM cancha WHERE id_complejo = %s AND nombre_cancha = %s",
                   (id_complejo, nombre_cancha), one=True)
    if not cancha:
        raise ErrorNegocio("Cancha no encontrada", 404)
    return cancha


def _datos_complejo():
    datos = datos_json()
    requeridos(datos, ["nombre", "direccion", "departamento"])
    return datos["nombre"], datos["direccion"], datos["departamento"]


def _datos_cancha(datos):
    requeridos(datos, ["superficie"])
    return (opcion(datos["superficie"], SUPERFICIES, "superficie"),
            booleano(datos.get("techada", False), "techada"))


# ---------- Complejos ----------

@bp.get("/complejos")
@cualquier_rol
def listar_complejos():
    return jsonify(query("""
        SELECT c.id_complejo, c.nombre, c.direccion, c.departamento,
               COUNT(ca.nombre_cancha) AS canchas
        FROM complejo c
        LEFT JOIN cancha ca ON ca.id_complejo = c.id_complejo
        GROUP BY c.id_complejo, c.nombre, c.direccion, c.departamento
        ORDER BY c.nombre
    """))


@bp.get("/complejos/<int:id_complejo>")
@cualquier_rol
def obtener_complejo(id_complejo):
    complejo = _buscar_complejo(id_complejo)
    complejo["canchas"] = query("""
        SELECT nombre_cancha, superficie, techada FROM cancha
        WHERE id_complejo = %s ORDER BY nombre_cancha
    """, (id_complejo,))
    return jsonify(complejo)


@bp.post("/complejos")
@solo_admin
def crear_complejo():
    id_complejo = execute("""
        INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s, %s, %s)
    """, _datos_complejo())
    return jsonify(mensaje="Complejo creado", id_complejo=id_complejo), 201


@bp.put("/complejos/<int:id_complejo>")
@solo_admin
def modificar_complejo(id_complejo):
    _buscar_complejo(id_complejo)
    execute("""
        UPDATE complejo SET nombre = %s, direccion = %s, departamento = %s
        WHERE id_complejo = %s
    """, _datos_complejo() + (id_complejo,))
    return jsonify(mensaje="Complejo modificado")


@bp.delete("/complejos/<int:id_complejo>")
@solo_admin
def eliminar_complejo(id_complejo):
    _buscar_complejo(id_complejo)
    execute("DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,))
    return jsonify(mensaje="Complejo eliminado")


# ---------- Canchas ----------

@bp.get("/canchas")
@cualquier_rol
def listar_canchas():
    return jsonify(query("""
        SELECT ca.nombre_cancha, ca.id_complejo, c.nombre AS complejo,
               ca.superficie, ca.techada
        FROM cancha ca
        JOIN complejo c ON c.id_complejo = ca.id_complejo
        ORDER BY c.nombre, ca.nombre_cancha
    """))


@bp.post("/complejos/<int:id_complejo>/canchas")
@solo_admin
def crear_cancha(id_complejo):
    _buscar_complejo(id_complejo)
    datos = datos_json()
    requeridos(datos, ["nombre_cancha"])
    execute("""
        INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada)
        VALUES (%s, %s, %s, %s)
    """, (datos["nombre_cancha"], id_complejo) + _datos_cancha(datos))
    return jsonify(mensaje="Cancha creada"), 201


@bp.put("/complejos/<int:id_complejo>/canchas/<nombre_cancha>")
@solo_admin
def modificar_cancha(id_complejo, nombre_cancha):
    _buscar_cancha(id_complejo, nombre_cancha)
    execute("""
        UPDATE cancha SET superficie = %s, techada = %s
        WHERE id_complejo = %s AND nombre_cancha = %s
    """, _datos_cancha(datos_json()) + (id_complejo, nombre_cancha))
    return jsonify(mensaje="Cancha modificada")


@bp.delete("/complejos/<int:id_complejo>/canchas/<nombre_cancha>")
@solo_admin
def eliminar_cancha(id_complejo, nombre_cancha):
    _buscar_cancha(id_complejo, nombre_cancha)
    execute("DELETE FROM cancha WHERE id_complejo = %s AND nombre_cancha = %s",
            (id_complejo, nombre_cancha))
    return jsonify(mensaje="Cancha eliminada")
