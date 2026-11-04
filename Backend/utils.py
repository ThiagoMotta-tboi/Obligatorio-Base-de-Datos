from datetime import date

from flask import request


class ErrorNegocio(Exception):
    """Error de una regla del torneo; se devuelve al cliente con su mensaje."""

    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def datos_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorNegocio("El cuerpo de la solicitud debe ser un objeto JSON")
    return datos


def requeridos(datos, campos):
    faltan = [c for c in campos if datos.get(c) in (None, "")]
    if faltan:
        raise ErrorNegocio(f"Faltan campos obligatorios: {', '.join(faltan)}")


def entero(valor, campo, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ErrorNegocio(f"{campo} debe ser un número entero")
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErrorNegocio(f"{campo} debe ser un número entero")
    if minimo is not None and numero < minimo:
        raise ErrorNegocio(f"{campo} debe ser mayor o igual a {minimo}")
    if maximo is not None and numero > maximo:
        raise ErrorNegocio(f"{campo} debe ser menor o igual a {maximo}")
    return numero


def fecha(valor, campo):
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        raise ErrorNegocio(f"{campo} debe tener el formato AAAA-MM-DD")


def opcion(valor, opciones, campo):
    if valor not in opciones:
        raise ErrorNegocio(f"Valor inválido para {campo}. Opciones: {', '.join(opciones)}")
    return valor


def booleano(valor, campo):
    if isinstance(valor, bool):
        return valor
    if valor in (0, 1):
        return bool(valor)
    raise ErrorNegocio(f"{campo} debe ser true o false")


def param_entero(nombre, requerido=True):
    valor = request.args.get(nombre)
    if valor in (None, ""):
        if requerido:
            raise ErrorNegocio(f"Falta el parámetro {nombre}")
        return None
    return entero(valor, nombre)
