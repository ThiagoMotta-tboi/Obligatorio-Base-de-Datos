from flask import Blueprint, jsonify, request

from auth import ADMINISTRADOR, cualquier_rol, rol_actual, solo_admin
from db import query, todos, transaccion, uno, uno_o_404
from sql_comun import RESULTADOS
from utils import ErrorNegocio, datos_json, entero, fecha, opcion, param_entero, requeridos

bp = Blueprint("partidos", __name__, url_prefix="/api/partidos")

ESTADOS = ("programado", "jugado", "postergado", "cancelado")
# Cambios de estado permitidos. Un postergado vuelve a 'programado' al reprogramarlo (PUT).
TRANSICIONES = {
    "programado": ("jugado", "postergado", "cancelado"),
    "postergado": ("cancelado",),
}
CAMPOS_PROGRAMACION = ["numero_fecha", "id_equipo_local", "id_equipo_visitante",
                       "dia", "id_turno", "nombre_cancha", "id_complejo"]
MIN_JUGADORES = 5

SELECT_PARTIDOS = f"""
    SELECT p.id_partido, p.id_torneo, p.numero_fecha, p.dia,
           p.id_turno, t.hora_inicio, t.hora_fin,
           p.id_complejo, co.nombre AS complejo, p.nombre_cancha,
           p.id_equipo_local, el.nombre AS equipo_local, r.goles_local,
           p.id_equipo_visitante, ev.nombre AS equipo_visitante, r.goles_visitante,
           p.estado, p.fecha_jugado
    FROM partido p
    JOIN equipo el   ON el.id_equipo = p.id_equipo_local
    JOIN equipo ev   ON ev.id_equipo = p.id_equipo_visitante
    JOIN turno t     ON t.id_turno = p.id_turno
    JOIN complejo co ON co.id_complejo = p.id_complejo
    LEFT JOIN ({RESULTADOS}) r ON r.id_partido = p.id_partido
"""


@bp.get("")
@cualquier_rol
def listar():
    """Filtros opcionales: id_torneo, numero_fecha, estado, pendientes=1 (ya disputados sin cerrar)."""
    condiciones, params = [], []
    for campo in ("id_torneo", "numero_fecha"):
        valor = param_entero(campo, requerido=False)
        if valor is not None:
            condiciones.append(f"p.{campo} = %s")
            params.append(valor)
    if request.args.get("estado"):
        condiciones.append("p.estado = %s")
        params.append(opcion(request.args["estado"], ESTADOS, "estado"))
    if request.args.get("pendientes") == "1":
        condiciones.append("p.estado = 'programado' AND TIMESTAMP(p.dia, t.hora_fin) <= NOW()")
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    return jsonify(query(f"""
        {SELECT_PARTIDOS}
        {where}
        ORDER BY p.numero_fecha, p.dia, t.hora_inicio
    """, params))


@bp.get("/<int:id_partido>")
@cualquier_rol
def obtener(id_partido):
    partido = query(f"{SELECT_PARTIDOS} WHERE p.id_partido = %s", (id_partido,), one=True)
    if not partido:
        raise ErrorNegocio("Partido no encontrado", 404)

    partido["planilla"] = query("""
        SELECT pp.id_equipo, e.nombre AS equipo, j.ci, j.nombre, j.apellido
        FROM planilla_partido pp
        JOIN jugador j ON j.ci = pp.ci_jugador
        JOIN equipo e  ON e.id_equipo = pp.id_equipo
        WHERE pp.id_partido = %s
        ORDER BY e.nombre, j.apellido
    """, (id_partido,))
    partido["goles"] = query("""
        SELECT g.id_gol, g.minuto, g.ci_jugador, j.nombre, j.apellido,
               pp.id_equipo, g.autogol
        FROM gol g
        JOIN jugador j ON j.ci = g.ci_jugador
        JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
        WHERE g.id_partido = %s
        ORDER BY g.minuto
    """, (id_partido,))
    partido["tarjetas"] = query("""
        SELECT t.id_tarjeta, t.minuto, t.ci_jugador, j.nombre, j.apellido,
               pp.id_equipo, t.color
        FROM tarjeta t
        JOIN jugador j ON j.ci = t.ci_jugador
        JOIN planilla_partido pp ON pp.id_partido = t.id_partido AND pp.ci_jugador = t.ci_jugador
        WHERE t.id_partido = %s
        ORDER BY t.minuto
    """, (id_partido,))
    return jsonify(partido)


def _leer_programacion(datos, base=None):
    """Combina los datos recibidos con los actuales (al modificar) y los valida."""
    valores = dict(base or {})
    valores.update({c: datos[c] for c in CAMPOS_PROGRAMACION if c in datos})
    requeridos(valores, CAMPOS_PROGRAMACION)
    return {
        "numero_fecha": entero(valores["numero_fecha"], "numero_fecha", minimo=1),
        "id_equipo_local": entero(valores["id_equipo_local"], "id_equipo_local"),
        "id_equipo_visitante": entero(valores["id_equipo_visitante"], "id_equipo_visitante"),
        "dia": fecha(valores["dia"], "dia"),
        "id_turno": entero(valores["id_turno"], "id_turno"),
        "nombre_cancha": str(valores["nombre_cancha"]),
        "id_complejo": entero(valores["id_complejo"], "id_complejo"),
    }


def _validar_programacion(cur, id_torneo, p, id_actual=0):
    """Reglas para programar un partido. id_actual excluye al propio partido al modificarlo."""
    torneo = uno_o_404(cur, "SELECT estado, fecha_inicio, fecha_fin FROM torneo WHERE id_torneo = %s",
                       (id_torneo,), "Torneo no encontrado")
    if torneo["estado"] == "finalizado":
        raise ErrorNegocio("El torneo ya finalizó", 409)

    local, visitante = p["id_equipo_local"], p["id_equipo_visitante"]
    if local == visitante:
        raise ErrorNegocio("Un equipo no puede enfrentarse a sí mismo")

    # Ambos equipos de la misma edición y con al menos 5 jugadores
    equipos = {e["id_equipo"]: e for e in todos(cur, """
        SELECT e.id_equipo, e.nombre, e.id_torneo, COUNT(ejt.ci_jugador) AS jugadores
        FROM equipo e
        LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
        WHERE e.id_equipo IN (%s, %s)
        GROUP BY e.id_equipo, e.nombre, e.id_torneo
    """, (local, visitante))}
    for id_equipo in (local, visitante):
        equipo = equipos.get(id_equipo)
        if not equipo or equipo["id_torneo"] != id_torneo:
            raise ErrorNegocio(f"El equipo {id_equipo} no pertenece a esta edición del torneo")
        if equipo["jugadores"] < MIN_JUGADORES:
            raise ErrorNegocio(f"{equipo['nombre']} tiene {equipo['jugadores']} jugadores; "
                               f"necesita al menos {MIN_JUGADORES}", 409)

    if not torneo["fecha_inicio"] <= p["dia"] <= torneo["fecha_fin"]:
        raise ErrorNegocio(f"El día debe estar entre {torneo['fecha_inicio']} y {torneo['fecha_fin']}")
    uno_o_404(cur, "SELECT 1 FROM turno WHERE id_turno = %s", (p["id_turno"],), "Turno no encontrado")
    uno_o_404(cur, "SELECT 1 FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s",
              (p["nombre_cancha"], p["id_complejo"]), "Cancha no encontrada")

    # No repetir rival salvo que el partido anterior esté cancelado
    previo = uno(cur, """
        SELECT id_partido, estado FROM partido
        WHERE id_torneo = %s AND estado <> 'cancelado' AND id_partido <> %s
          AND LEAST(id_equipo_local, id_equipo_visitante)    = LEAST(%s, %s)
          AND GREATEST(id_equipo_local, id_equipo_visitante) = GREATEST(%s, %s)
    """, (id_torneo, id_actual, local, visitante, local, visitante))
    if previo:
        raise ErrorNegocio(f"Estos equipos ya tienen un partido en esta edición "
                           f"(partido {previo['id_partido']}, {previo['estado']})", 409)

    # Un solo partido por equipo en cada fecha
    otro = uno(cur, """
        SELECT p.id_partido, el.nombre AS local, ev.nombre AS visitante
        FROM partido p
        JOIN equipo el ON el.id_equipo = p.id_equipo_local
        JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante
        WHERE p.id_torneo = %s AND p.numero_fecha = %s
          AND p.estado <> 'cancelado' AND p.id_partido <> %s
          AND (p.id_equipo_local IN (%s, %s) OR p.id_equipo_visitante IN (%s, %s))
    """, (id_torneo, p["numero_fecha"], id_actual, local, visitante, local, visitante))
    if otro:
        raise ErrorNegocio(f"Uno de los equipos ya juega en la fecha {p['numero_fecha']} "
                           f"({otro['local']} vs {otro['visitante']})", 409)

    # La cancha no puede tener dos partidos en el mismo día y turno
    ocupada = uno(cur, """
        SELECT id_partido FROM partido
        WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s AND id_complejo = %s
          AND estado IN ('programado', 'jugado') AND id_partido <> %s
    """, (p["dia"], p["id_turno"], p["nombre_cancha"], p["id_complejo"], id_actual))
    if ocupada:
        raise ErrorNegocio(f"La cancha ya está ocupada ese día y turno (partido {ocupada['id_partido']})", 409)


@bp.post("")
@solo_admin
def crear():
    datos = datos_json()
    requeridos(datos, ["id_torneo"])
    id_torneo = entero(datos["id_torneo"], "id_torneo")
    p = _leer_programacion(datos)

    with transaccion() as cur:
        _validar_programacion(cur, id_torneo, p)
        cur.execute("""
            INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                                 dia, id_turno, nombre_cancha, id_complejo, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'programado')
        """, (id_torneo, p["numero_fecha"], p["id_equipo_local"], p["id_equipo_visitante"],
              p["dia"], p["id_turno"], p["nombre_cancha"], p["id_complejo"]))
        id_partido = cur.lastrowid
    return jsonify(mensaje="Partido programado", id_partido=id_partido), 201


@bp.put("/<int:id_partido>")
@solo_admin
def modificar(id_partido):
    """Reprograma un partido programado o postergado; queda en estado 'programado'."""
    datos = datos_json()
    with transaccion() as cur:
        actual = uno_o_404(cur, "SELECT * FROM partido WHERE id_partido = %s",
                           (id_partido,), "Partido no encontrado")
        if actual["estado"] not in ("programado", "postergado"):
            raise ErrorNegocio(f"Un partido {actual['estado']} no puede reprogramarse", 409)
        if uno(cur, "SELECT 1 FROM planilla_partido WHERE id_partido = %s LIMIT 1", (id_partido,)):
            raise ErrorNegocio("El partido ya tiene planilla cargada; no puede reprogramarse", 409)

        p = _leer_programacion(datos, base=actual)
        _validar_programacion(cur, actual["id_torneo"], p, id_actual=id_partido)
        cur.execute("""
            UPDATE partido
            SET numero_fecha = %s, id_equipo_local = %s, id_equipo_visitante = %s, dia = %s,
                id_turno = %s, nombre_cancha = %s, id_complejo = %s, estado = 'programado'
            WHERE id_partido = %s
        """, (p["numero_fecha"], p["id_equipo_local"], p["id_equipo_visitante"], p["dia"],
              p["id_turno"], p["nombre_cancha"], p["id_complejo"], id_partido))
    return jsonify(mensaje="Partido reprogramado")


@bp.put("/<int:id_partido>/estado")
@cualquier_rol
def cambiar_estado(id_partido):
    """El planillero solo puede cerrar el partido (marcarlo como jugado)."""
    datos = datos_json()
    requeridos(datos, ["estado"])
    nuevo = opcion(datos["estado"], ESTADOS, "estado")
    if nuevo != "jugado" and rol_actual() != ADMINISTRADOR:
        raise ErrorNegocio("Solo un administrador puede postergar o cancelar partidos", 403)

    with transaccion() as cur:
        partido = uno_o_404(cur, """
            SELECT p.estado,
                   TIMESTAMP(p.dia, t.hora_fin) AS fin,
                   TIMESTAMP(p.dia, t.hora_fin) <= NOW() AS disputado,
                   (SELECT COUNT(*) FROM planilla_partido pp WHERE pp.id_partido = p.id_partido) AS en_planilla
            FROM partido p
            JOIN turno t ON t.id_turno = p.id_turno
            WHERE p.id_partido = %s
        """, (id_partido,), "Partido no encontrado")

        if nuevo not in TRANSICIONES.get(partido["estado"], ()):
            raise ErrorNegocio(f"No se puede pasar de '{partido['estado']}' a '{nuevo}'", 409)

        if nuevo == "jugado":
            if not partido["disputado"]:
                raise ErrorNegocio("El partido solo puede marcarse como jugado cuando su día y turno ya pasaron", 409)
            # fecha_jugado = fin del turno; desde ahí corren las 48 horas para corregir
            cur.execute("UPDATE partido SET estado = 'jugado', fecha_jugado = %s WHERE id_partido = %s",
                        (partido["fin"], id_partido))
        else:
            if partido["en_planilla"]:
                raise ErrorNegocio("El partido tiene planilla cargada; no puede postergarse ni cancelarse", 409)
            cur.execute("UPDATE partido SET estado = %s WHERE id_partido = %s", (nuevo, id_partido))
    return jsonify(mensaje=f"El partido pasó a '{nuevo}'")


@bp.delete("/<int:id_partido>")
@solo_admin
def eliminar(id_partido):
    with transaccion() as cur:
        partido = uno_o_404(cur, "SELECT estado FROM partido WHERE id_partido = %s",
                            (id_partido,), "Partido no encontrado")
        if partido["estado"] == "jugado":
            raise ErrorNegocio("Un partido jugado no puede eliminarse", 409)
        if uno(cur, "SELECT 1 FROM planilla_partido WHERE id_partido = %s LIMIT 1", (id_partido,)):
            raise ErrorNegocio("El partido tiene planilla cargada; elimínela primero", 409)
        cur.execute("DELETE FROM partido WHERE id_partido = %s", (id_partido,))
    return jsonify(mensaje="Partido eliminado")
