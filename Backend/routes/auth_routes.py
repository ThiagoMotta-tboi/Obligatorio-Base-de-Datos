import bcrypt
from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity

from auth import cualquier_rol
from db import query
from utils import ErrorNegocio, datos_json, requeridos

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    datos = datos_json()
    requeridos(datos, ["correo", "password"])

    usuario = query("SELECT correo, password, rol FROM login WHERE correo = %s",
                    (datos["correo"],), one=True)
    if not usuario or not _password_valida(datos["password"], usuario["password"]):
        raise ErrorNegocio("Correo o contraseña incorrectos", 401)

    token = create_access_token(identity=usuario["correo"],
                                additional_claims={"rol": usuario["rol"]})
    return jsonify(token=token, correo=usuario["correo"], rol=usuario["rol"])


@bp.get("/me")
@cualquier_rol
def me():
    return jsonify(correo=get_jwt_identity(), rol=get_jwt().get("rol"))


def _password_valida(password, hash_guardado):
    try:
        return bcrypt.checkpw(password.encode(), hash_guardado.encode())
    except ValueError:  # el valor guardado no es un hash bcrypt válido
        return False
