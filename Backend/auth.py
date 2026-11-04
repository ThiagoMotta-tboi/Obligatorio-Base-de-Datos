from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required

ADMINISTRADOR = "administrador"
PLANILLERO = "planillero"


def rol_requerido(*roles):
    """Exige un token válido y que el rol del usuario esté entre los indicados."""

    def decorador(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if get_jwt().get("rol") not in roles:
                return jsonify(error="No tiene permisos para esta acción"), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorador


def rol_actual():
    return get_jwt().get("rol")


solo_admin = rol_requerido(ADMINISTRADOR)
cualquier_rol = rol_requerido(ADMINISTRADOR, PLANILLERO)
