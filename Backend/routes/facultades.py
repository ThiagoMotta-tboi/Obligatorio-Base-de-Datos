from flask import Blueprint, jsonify

from auth import cualquier_rol, solo_admin
from db import execute, query
from utils import ErrorNegocio, datos_json, requeridos

bp = Blueprint("facultades", __name__, url_prefix="/api/facultades")


def _buscar(id_facultad):
    facultad = query("SELECT id_facultad, nombre FROM facultad WHERE id_facultad = %s",
                     (id_facultad,), one=True)
    if not facultad:
        raise ErrorNegocio("Facultad no encontrada", 404)
    return facultad


@bp.get("")
@cualquier_rol
def listar():
    return jsonify(query("SELECT id_facultad, nombre FROM facultad ORDER BY nombre"))


@bp.get("/<int:id_facultad>")
@cualquier_rol
def obtener(id_facultad):
    return jsonify(_buscar(id_facultad))


@bp.post("")
@solo_admin
def crear():
    datos = datos_json()
    requeridos(datos, ["nombre"])
    id_facultad = execute("INSERT INTO facultad (nombre) VALUES (%s)", (datos["nombre"],))
    return jsonify(mensaje="Facultad creada", id_facultad=id_facultad), 201


@bp.put("/<int:id_facultad>")
@solo_admin
def modificar(id_facultad):
    _buscar(id_facultad)
    datos = datos_json()
    requeridos(datos, ["nombre"])
    execute("UPDATE facultad SET nombre = %s WHERE id_facultad = %s",
            (datos["nombre"], id_facultad))
    return jsonify(mensaje="Facultad modificada")


@bp.delete("/<int:id_facultad>")
@solo_admin
def eliminar(id_facultad):
    _buscar(id_facultad)
    execute("DELETE FROM facultad WHERE id_facultad = %s", (id_facultad,))
    return jsonify(mensaje="Facultad eliminada")
