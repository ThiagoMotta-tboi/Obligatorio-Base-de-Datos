from flask import Blueprint, jsonify

from auth import cualquier_rol, solo_admin
from db import execute, query, todos, transaccion, uno_o_404
from utils import ErrorNegocio, datos_json, entero, fecha, opcion, requeridos

bp = Blueprint("torneos", __name__, url_prefix="/api/torneos")

ESTADOS = ("inscripcion", "en curso", "finalizado")
# Las etapas avanzan en un solo sentido
SIGUIENTE_ESTADO = {"inscripcion": "en curso", "en curso": "finalizado"}


def _validar(datos):
    requeridos(datos, ["nombre", "anio", "semestre", "fecha_inicio", "fecha_fin"])
    inicio = fecha(datos["fecha_inicio"], "fecha_inicio")
    fin = fecha(datos["fecha_fin"], "fecha_fin")
    if fin < inicio:
        raise ErrorNegocio("La fecha de fin no puede ser anterior a la de inicio")
    return (datos["nombre"], entero(datos["anio"], "anio", minimo=2000),
            entero(datos["semestre"], "semestre", minimo=1, maximo=2), inicio, fin)


@bp.get("")
@cualquier_rol
def listar():
    return jsonify(query("""
        SELECT t.id_torneo, t.nombre, t.anio, t.semestre, t.fecha_inicio, t.fecha_fin, t.estado,
               (SELECT COUNT(*) FROM equipo e WHERE e.id_torneo = t.id_torneo) AS equipos
        FROM torneo t
        ORDER BY t.anio DESC, t.semestre DESC
    """))


@bp.get("/<int:id_torneo>")
@cualquier_rol
def obtener(id_torneo):
    torneo = query("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,), one=True)
    if not torneo:
        raise ErrorNegocio("Torneo no encontrado", 404)
    return jsonify(torneo)


@bp.post("")
@solo_admin
def crear():
    id_torneo = execute("""
        INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin, estado)
        VALUES (%s, %s, %s, %s, %s, 'inscripcion')
    """, _validar(datos_json()))
    return jsonify(mensaje="Torneo creado", id_torneo=id_torneo), 201


@bp.put("/<int:id_torneo>")
@solo_admin
def modificar(id_torneo):
    valores = _validar(datos_json())
    with transaccion() as cur:
        uno_o_404(cur, "SELECT 1 FROM torneo WHERE id_torneo = %s", (id_torneo,), "Torneo no encontrado")
        cur.execute("""
            UPDATE torneo SET nombre = %s, anio = %s, semestre = %s, fecha_inicio = %s, fecha_fin = %s
            WHERE id_torneo = %s
        """, valores + (id_torneo,))
    return jsonify(mensaje="Torneo modificado")


@bp.put("/<int:id_torneo>/estado")
@solo_admin
def cambiar_estado(id_torneo):
    datos = datos_json()
    requeridos(datos, ["estado"])
    nuevo = opcion(datos["estado"], ESTADOS, "estado")

    with transaccion() as cur:
        torneo = uno_o_404(cur, "SELECT estado FROM torneo WHERE id_torneo = %s",
                           (id_torneo,), "Torneo no encontrado")
        if SIGUIENTE_ESTADO.get(torneo["estado"]) != nuevo:
            raise ErrorNegocio(f"No se puede pasar de '{torneo['estado']}' a '{nuevo}'", 409)

        if nuevo == "en curso":
            _validar_inicio(cur, id_torneo)
        else:
            pendientes = todos(cur, """
                SELECT id_partido FROM partido
                WHERE id_torneo = %s AND estado IN ('programado', 'postergado')
            """, (id_torneo,))
            if pendientes:
                raise ErrorNegocio(f"Hay {len(pendientes)} partido(s) programados o postergados", 409)

        cur.execute("UPDATE torneo SET estado = %s WHERE id_torneo = %s", (nuevo, id_torneo))
    return jsonify(mensaje=f"El torneo pasó a '{nuevo}'")


def _validar_inicio(cur, id_torneo):
    """Para comenzar el torneo todos los planteles deben estar completos."""
    equipos = todos(cur, """
        SELECT e.nombre, e.ci_capitan, COUNT(ejt.ci_jugador) AS jugadores
        FROM equipo e
        LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo, e.nombre, e.ci_capitan
    """, (id_torneo,))
    if len(equipos) < 2:
        raise ErrorNegocio("El torneo necesita al menos 2 equipos para comenzar", 409)

    problemas = []
    for e in equipos:
        if not 5 <= e["jugadores"] <= 10:
            problemas.append(f"{e['nombre']} tiene {e['jugadores']} jugadores (deben ser entre 5 y 10)")
        if e["ci_capitan"] is None:
            problemas.append(f"{e['nombre']} no tiene capitán")
    if problemas:
        raise ErrorNegocio("No se puede iniciar el torneo: " + "; ".join(problemas), 409)


@bp.delete("/<int:id_torneo>")
@solo_admin
def eliminar(id_torneo):
    if not query("SELECT 1 FROM torneo WHERE id_torneo = %s", (id_torneo,), one=True):
        raise ErrorNegocio("Torneo no encontrado", 404)
    execute("DELETE FROM torneo WHERE id_torneo = %s", (id_torneo,))
    return jsonify(mensaje="Torneo eliminado")
