"""Planilla de juego, goles y tarjetas de un partido (lo que carga el planillero)."""
from flask import Blueprint, jsonify

from auth import cualquier_rol
from db import query, todos, transaccion, uno, uno_o_404
from sql_comun import SANCION_VIGENTE
from utils import ErrorNegocio, booleano, datos_json, entero, opcion, requeridos

bp = Blueprint("planillas", __name__, url_prefix="/api/partidos")

COLORES = ("amarilla", "roja")
AMARILLAS_PARA_SANCION = 3


def _partido_editable(cur, id_partido):
    """La planilla se carga cuando el partido ya se disputó y, si está jugado, dentro de las 48 horas."""
    partido = uno_o_404(cur, """
        SELECT p.id_partido, p.id_torneo, p.numero_fecha, p.estado,
               p.id_equipo_local, p.id_equipo_visitante,
               TIMESTAMP(p.dia, t.hora_fin) <= NOW() AS disputado,
               (p.fecha_jugado IS NULL OR NOW() <= p.fecha_jugado + INTERVAL 48 HOUR) AS en_plazo
        FROM partido p
        JOIN turno t ON t.id_turno = p.id_turno
        WHERE p.id_partido = %s
    """, (id_partido,), "Partido no encontrado")

    if partido["estado"] in ("postergado", "cancelado"):
        raise ErrorNegocio(f"El partido está {partido['estado']}; no admite planilla", 409)
    if not partido["disputado"]:
        raise ErrorNegocio("El partido todavía no se disputó", 409)
    if partido["estado"] == "jugado" and not partido["en_plazo"]:
        raise ErrorNegocio("Pasaron más de 48 horas desde el partido; su planilla ya no puede corregirse", 409)
    return partido


def _verificar_en_planilla(cur, id_partido, ci):
    if not uno(cur, "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
               (id_partido, ci)):
        raise ErrorNegocio("Solo pueden registrarse goles y tarjetas de jugadores que figuren en la planilla")


def _existe_partido(id_partido):
    if not query("SELECT 1 FROM partido WHERE id_partido = %s", (id_partido,), one=True):
        raise ErrorNegocio("Partido no encontrado", 404)


# ---------- Planilla ----------

@bp.get("/<int:id_partido>/jugadores")
@cualquier_rol
def jugadores_del_partido(id_partido):
    """Planteles de ambos equipos, indicando quién está suspendido y quién ya figura en la planilla."""
    _existe_partido(id_partido)
    return jsonify(query("""
        SELECT ejt.id_equipo, e.nombre AS equipo, ejt.numero_camiseta,
               j.ci, j.nombre, j.apellido,
               EXISTS (SELECT 1 FROM planilla_partido pp
                       WHERE pp.id_partido = p.id_partido AND pp.ci_jugador = j.ci) AS en_planilla,
               EXISTS (SELECT 1 FROM sancion_jugador s
                       WHERE s.ci_jugador = j.ci AND s.id_torneo = p.id_torneo
                         AND p.numero_fecha BETWEEN s.numero_fecha_inicio
                                                AND s.numero_fecha_inicio + s.cantidad_fechas - 1) AS suspendido
        FROM partido p
        JOIN equipo_jugador_torneo ejt ON ejt.id_torneo = p.id_torneo
                                      AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
        JOIN jugador j ON j.ci = ejt.ci_jugador
        JOIN equipo e  ON e.id_equipo = ejt.id_equipo
        WHERE p.id_partido = %s
        ORDER BY ejt.id_equipo = p.id_equipo_visitante, ejt.numero_camiseta
    """, (id_partido,)))


@bp.get("/<int:id_partido>/planilla")
@cualquier_rol
def ver_planilla(id_partido):
    _existe_partido(id_partido)
    return jsonify(query("""
        SELECT pp.id_equipo, e.nombre AS equipo, j.ci, j.nombre, j.apellido
        FROM planilla_partido pp
        JOIN jugador j ON j.ci = pp.ci_jugador
        JOIN equipo e  ON e.id_equipo = pp.id_equipo
        WHERE pp.id_partido = %s
        ORDER BY e.nombre, j.apellido
    """, (id_partido,)))


@bp.post("/<int:id_partido>/planilla")
@cualquier_rol
def agregar_a_planilla(id_partido):
    """Acepta {"ci_jugador": 123} o {"ci_jugadores": [123, 456, ...]}."""
    datos = datos_json()
    if "ci_jugadores" in datos:
        lista = datos["ci_jugadores"]
        if not isinstance(lista, list) or not lista:
            raise ErrorNegocio("ci_jugadores debe ser una lista con al menos una cédula")
    else:
        requeridos(datos, ["ci_jugador"])
        lista = [datos["ci_jugador"]]
    cedulas = [entero(ci, "ci_jugador") for ci in lista]

    with transaccion() as cur:
        partido = _partido_editable(cur, id_partido)
        for ci in cedulas:
            _agregar_jugador(cur, partido, ci)
    return jsonify(mensaje=f"{len(cedulas)} jugador(es) agregado(s) a la planilla"), 201


def _agregar_jugador(cur, partido, ci):
    inscripcion = uno(cur, """
        SELECT id_equipo FROM equipo_jugador_torneo
        WHERE ci_jugador = %s AND id_torneo = %s AND id_equipo IN (%s, %s)
    """, (ci, partido["id_torneo"], partido["id_equipo_local"], partido["id_equipo_visitante"]))
    if not inscripcion:
        raise ErrorNegocio(f"El jugador {ci} no pertenece al plantel de ninguno de los dos equipos")

    if uno(cur, "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
           (partido["id_partido"], ci)):
        raise ErrorNegocio(f"El jugador {ci} ya figura en la planilla", 409)

    sancion = uno(cur, SANCION_VIGENTE, (ci, partido["id_torneo"], partido["numero_fecha"]))
    if sancion:
        raise ErrorNegocio(f"El jugador {ci} está suspendido de la fecha {sancion['numero_fecha_inicio']} "
                           f"a la {sancion['numero_fecha_fin']} (motivo: {sancion['motivo']})", 409)

    cur.execute("""
        INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)
    """, (partido["id_partido"], ci, inscripcion["id_equipo"]))


@bp.delete("/<int:id_partido>/planilla/<int:ci>")
@cualquier_rol
def quitar_de_planilla(id_partido, ci):
    with transaccion() as cur:
        _partido_editable(cur, id_partido)
        uno_o_404(cur, "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
                  (id_partido, ci), "El jugador no figura en la planilla")
        if uno(cur, """
            SELECT 1 FROM gol WHERE id_partido = %s AND ci_jugador = %s
            UNION ALL
            SELECT 1 FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s
            LIMIT 1
        """, (id_partido, ci, id_partido, ci)):
            raise ErrorNegocio("El jugador tiene goles o tarjetas registrados; elimínelos primero", 409)
        cur.execute("DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
                    (id_partido, ci))
    return jsonify(mensaje="Jugador quitado de la planilla")


# ---------- Goles ----------

def _datos_gol(datos):
    requeridos(datos, ["ci_jugador", "minuto"])
    return (entero(datos["ci_jugador"], "ci_jugador"),
            entero(datos["minuto"], "minuto", minimo=0, maximo=60),
            booleano(datos.get("autogol", False), "autogol"))


@bp.get("/<int:id_partido>/goles")
@cualquier_rol
def listar_goles(id_partido):
    _existe_partido(id_partido)
    return jsonify(query("""
        SELECT g.id_gol, g.minuto, g.ci_jugador, j.nombre, j.apellido, pp.id_equipo, g.autogol
        FROM gol g
        JOIN jugador j ON j.ci = g.ci_jugador
        JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
        WHERE g.id_partido = %s
        ORDER BY g.minuto
    """, (id_partido,)))


@bp.post("/<int:id_partido>/goles")
@cualquier_rol
def registrar_gol(id_partido):
    ci, minuto, autogol = _datos_gol(datos_json())
    with transaccion() as cur:
        _partido_editable(cur, id_partido)
        _verificar_en_planilla(cur, id_partido, ci)
        cur.execute("""
            INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s, %s, %s, %s)
        """, (id_partido, ci, minuto, autogol))
        id_gol = cur.lastrowid
    return jsonify(mensaje="Gol registrado", id_gol=id_gol), 201


@bp.put("/<int:id_partido>/goles/<int:id_gol>")
@cualquier_rol
def modificar_gol(id_partido, id_gol):
    ci, minuto, autogol = _datos_gol(datos_json())
    with transaccion() as cur:
        _partido_editable(cur, id_partido)
        uno_o_404(cur, "SELECT 1 FROM gol WHERE id_gol = %s AND id_partido = %s",
                  (id_gol, id_partido), "Gol no encontrado")
        _verificar_en_planilla(cur, id_partido, ci)
        cur.execute("""
            UPDATE gol SET ci_jugador = %s, minuto = %s, autogol = %s WHERE id_gol = %s
        """, (ci, minuto, autogol, id_gol))
    return jsonify(mensaje="Gol modificado")


@bp.delete("/<int:id_partido>/goles/<int:id_gol>")
@cualquier_rol
def eliminar_gol(id_partido, id_gol):
    with transaccion() as cur:
        _partido_editable(cur, id_partido)
        uno_o_404(cur, "SELECT 1 FROM gol WHERE id_gol = %s AND id_partido = %s",
                  (id_gol, id_partido), "Gol no encontrado")
        cur.execute("DELETE FROM gol WHERE id_gol = %s", (id_gol,))
    return jsonify(mensaje="Gol eliminado")


# ---------- Tarjetas y sanciones automáticas ----------

@bp.get("/<int:id_partido>/tarjetas")
@cualquier_rol
def listar_tarjetas(id_partido):
    _existe_partido(id_partido)
    return jsonify(query("""
        SELECT t.id_tarjeta, t.minuto, t.ci_jugador, j.nombre, j.apellido, pp.id_equipo, t.color
        FROM tarjeta t
        JOIN jugador j ON j.ci = t.ci_jugador
        JOIN planilla_partido pp ON pp.id_partido = t.id_partido AND pp.ci_jugador = t.ci_jugador
        WHERE t.id_partido = %s
        ORDER BY t.minuto
    """, (id_partido,)))


@bp.post("/<int:id_partido>/tarjetas")
@cualquier_rol
def registrar_tarjeta(id_partido):
    datos = datos_json()
    requeridos(datos, ["ci_jugador", "minuto", "color"])
    ci = entero(datos["ci_jugador"], "ci_jugador")
    minuto = entero(datos["minuto"], "minuto", minimo=0, maximo=60)
    color = opcion(datos["color"], COLORES, "color")

    with transaccion() as cur:
        partido = _partido_editable(cur, id_partido)
        _verificar_en_planilla(cur, id_partido, ci)
        if color == "roja" and uno(cur, """
            SELECT 1 FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s AND color = 'roja'
        """, (id_partido, ci)):
            raise ErrorNegocio("El jugador ya recibió una tarjeta roja en este partido", 409)

        cur.execute("""
            INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s, %s, %s, %s)
        """, (id_partido, ci, minuto, color))
        id_tarjeta = cur.lastrowid

        if color == "roja":
            # Roja: una fecha de suspensión, que se cumple en la fecha siguiente
            cur.execute("""
                INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio,
                                             cantidad_fechas, id_tarjeta_origen)
                VALUES (%s, %s, 'roja', %s, 1, %s)
            """, (ci, partido["id_torneo"], partido["numero_fecha"] + 1, id_tarjeta))
        else:
            recalcular_sanciones_amarillas(cur, ci, partido["id_torneo"])

        sancion = uno(cur, "SELECT id_sancion, motivo, numero_fecha_inicio FROM sancion_jugador "
                           "WHERE id_tarjeta_origen = %s", (id_tarjeta,))

    respuesta = {"mensaje": "Tarjeta registrada", "id_tarjeta": id_tarjeta, "sancion_generada": sancion}
    return jsonify(respuesta), 201


@bp.delete("/<int:id_partido>/tarjetas/<int:id_tarjeta>")
@cualquier_rol
def eliminar_tarjeta(id_partido, id_tarjeta):
    with transaccion() as cur:
        partido = _partido_editable(cur, id_partido)
        tarjeta = uno_o_404(cur, "SELECT ci_jugador, color FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s",
                            (id_tarjeta, id_partido), "Tarjeta no encontrada")
        # La sanción por roja se borra sola (ON DELETE CASCADE en id_tarjeta_origen)
        cur.execute("DELETE FROM tarjeta WHERE id_tarjeta = %s", (id_tarjeta,))
        if tarjeta["color"] == "amarilla":
            recalcular_sanciones_amarillas(cur, tarjeta["ci_jugador"], partido["id_torneo"])
    return jsonify(mensaje="Tarjeta eliminada")


def recalcular_sanciones_amarillas(cur, ci, id_torneo):
    """Regenera las sanciones por acumulación: una cada 3 amarillas de la edición.

    Se recalcula desde cero para que agregar o quitar cualquier amarilla
    deje las sanciones consistentes.
    """
    cur.execute("""
        DELETE FROM sancion_jugador
        WHERE ci_jugador = %s AND id_torneo = %s AND motivo = 'acumulacion de amarillas'
    """, (ci, id_torneo))

    amarillas = todos(cur, """
        SELECT t.id_tarjeta, p.numero_fecha
        FROM tarjeta t
        JOIN partido p ON p.id_partido = t.id_partido
        WHERE t.ci_jugador = %s AND p.id_torneo = %s AND t.color = 'amarilla'
        ORDER BY p.numero_fecha, t.minuto, t.id_tarjeta
    """, (ci, id_torneo))

    for posicion, amarilla in enumerate(amarillas, start=1):
        if posicion % AMARILLAS_PARA_SANCION == 0:
            cur.execute("""
                INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio,
                                             cantidad_fechas, id_tarjeta_origen)
                VALUES (%s, %s, 'acumulacion de amarillas', %s, 1, %s)
            """, (ci, id_torneo, amarilla["numero_fecha"] + 1, amarilla["id_tarjeta"]))
