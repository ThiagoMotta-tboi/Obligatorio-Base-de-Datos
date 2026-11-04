from flask import Blueprint, jsonify

from auth import cualquier_rol
from db import query

bp = Blueprint("turnos", __name__, url_prefix="/api/turnos")


@bp.get("")
@cualquier_rol
def listar():
    return jsonify(query("SELECT id_turno, hora_inicio, hora_fin FROM turno ORDER BY hora_inicio"))
