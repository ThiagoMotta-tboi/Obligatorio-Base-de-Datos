from datetime import date

from flask import Blueprint, jsonify, request

from auth import cualquier_rol, solo_admin
from db import execute, query, transaccion, uno, uno_o_404
from utils import ErrorNegocio, datos_json, entero, fecha, opcion, param_entero, requeridos

bp = Blueprint("jugadores", __name__, url_prefix="/api/jugadores")

TIPOS = ("grado", "posgrado", "docente", "funcionario")
CAMPOS = ["nombre", "apellido", "email", "fecha_nacimiento", "id_facultad", "tipo"]


def _validar(datos):
    requeridos(datos, CAMPOS)
    if "@" not in str(datos["email"]):
        raise ErrorNegocio("El email no es válido")
    nacimiento = fecha(datos["fecha_nacimiento"], "fecha_nacimiento")
    if nacimiento >= date.today():
        raise ErrorNegocio("La fecha de nacimiento debe ser anterior a hoy")
    return (datos["nombre"], datos["apellido"], datos["email"], nacimiento,
            entero(datos["id_facultad"], "id_facultad"), opcion(datos["tipo"], TIPOS, "tipo"))


@bp.get("")
@cualquier_rol
def listar():
    condiciones, params = [], []
    id_facultad = param_entero("id_facultad", requerido=False)
    if id_facultad is not None:
        condiciones.append("j.id_facultad = %s")
        params.append(id_facultad)
    tipo = request.args.get("tipo")
    if tipo:
        condiciones.append("j.tipo = %s")
        params.append(opcion(tipo, TIPOS, "tipo"))
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    return jsonify(query(f"""
        SELECT j.ci, j.nombre, j.apellido, j.email, j.fecha_nacimiento,
               j.tipo, j.id_facultad, f.nombre AS facultad
        FROM jugador j
        JOIN facultad f ON f.id_facultad = j.id_facultad
        {where}
        ORDER BY j.apellido, j.nombre
    """, params))


@bp.get("/<int:ci>")
@cualquier_rol
def obtener(ci):
    jugador = query("""
        SELECT j.ci, j.nombre, j.apellido, j.email, j.fecha_nacimiento,
               j.tipo, j.id_facultad, f.nombre AS facultad
        FROM jugador j
        JOIN facultad f ON f.id_facultad = j.id_facultad
        WHERE j.ci = %s
    """, (ci,), one=True)
    if not jugador:
        raise ErrorNegocio("Jugador no encontrado", 404)

    jugador["equipos"] = query("""
        SELECT t.id_torneo, t.nombre AS torneo, e.id_equipo, e.nombre AS equipo,
               ejt.numero_camiseta
        FROM equipo_jugador_torneo ejt
        JOIN equipo e ON e.id_equipo = ejt.id_equipo
        JOIN torneo t ON t.id_torneo = ejt.id_torneo
        WHERE ejt.ci_jugador = %s
        ORDER BY t.anio DESC, t.semestre DESC
    """, (ci,))
    return jsonify(jugador)


@bp.post("")
@solo_admin
def crear():
    datos = datos_json()
    requeridos(datos, ["ci"])
    ci = entero(datos["ci"], "ci", minimo=1)
    execute("""
        INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (ci,) + _validar(datos))
    return jsonify(mensaje="Jugador creado", ci=ci), 201


@bp.put("/<int:ci>")
@solo_admin
def modificar(ci):
    valores = _validar(datos_json())
    with transaccion() as cur:
        actual = uno_o_404(cur, "SELECT id_facultad FROM jugador WHERE ci = %s",
                           (ci,), "Jugador no encontrado")
        nueva_facultad = valores[4]
        if nueva_facultad != actual["id_facultad"] and uno(
                cur, "SELECT 1 FROM equipo_jugador_torneo WHERE ci_jugador = %s LIMIT 1", (ci,)):
            raise ErrorNegocio("No se puede cambiar la facultad de un jugador que integra un plantel", 409)
        cur.execute("""
            UPDATE jugador
            SET nombre = %s, apellido = %s, email = %s, fecha_nacimiento = %s,
                id_facultad = %s, tipo = %s
            WHERE ci = %s
        """, valores + (ci,))
    return jsonify(mensaje="Jugador modificado")


@bp.delete("/<int:ci>")
@solo_admin
def eliminar(ci):
    if not query("SELECT 1 FROM jugador WHERE ci = %s", (ci,), one=True):
        raise ErrorNegocio("Jugador no encontrado", 404)
    execute("DELETE FROM jugador WHERE ci = %s", (ci,))
    return jsonify(mensaje="Jugador eliminado")
