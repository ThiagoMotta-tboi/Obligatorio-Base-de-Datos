"""Reportes del área de deportes. Todos reciben ?id_torneo=N salvo que se indique otra cosa."""
from flask import Blueprint, jsonify

from auth import cualquier_rol
from db import query
from sql_comun import RESULTADOS
from utils import param_entero

bp = Blueprint("reportes", __name__, url_prefix="/api/reportes")


@bp.get("/posiciones")
@cualquier_rol
def posiciones():
    id_torneo = param_entero("id_torneo")
    return jsonify(query(f"""
        WITH res AS ({RESULTADOS}),
        r AS (
            SELECT id_equipo_local AS id_equipo, goles_local AS gf, goles_visitante AS gc FROM res
            UNION ALL
            SELECT id_equipo_visitante, goles_visitante, goles_local FROM res
        )
        SELECT e.id_equipo, e.nombre AS equipo,
               COUNT(r.id_equipo)                                  AS pj,
               COALESCE(SUM(r.gf > r.gc), 0)                       AS pg,
               COALESCE(SUM(r.gf = r.gc), 0)                       AS pe,
               COALESCE(SUM(r.gf < r.gc), 0)                       AS pp,
               COALESCE(SUM(r.gf), 0)                              AS gf,
               COALESCE(SUM(r.gc), 0)                              AS gc,
               COALESCE(SUM(r.gf - r.gc), 0)                       AS dg,
               COALESCE(SUM(3 * (r.gf > r.gc) + (r.gf = r.gc)), 0) AS pts
        FROM equipo e
        LEFT JOIN r ON r.id_equipo = e.id_equipo
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo, e.nombre
        ORDER BY pts DESC, dg DESC, gf DESC, e.nombre
    """, (id_torneo,)))


@bp.get("/goleadores")
@cualquier_rol
def goleadores():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, COUNT(*) AS goles
        FROM gol g
        JOIN partido p ON p.id_partido = g.id_partido
        JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
        JOIN jugador j ON j.ci = g.ci_jugador
        JOIN equipo e  ON e.id_equipo = pp.id_equipo
        WHERE p.id_torneo = %s AND p.estado = 'jugado' AND g.autogol = FALSE
        GROUP BY j.ci, j.nombre, j.apellido, e.nombre
        ORDER BY goles DESC, j.apellido
        LIMIT 10
    """, (id_torneo,)))


@bp.get("/fair-play")
@cualquier_rol
def fair_play():
    """1 punto por amarilla y 3 por roja; el mejor equipo es el de menor puntaje."""
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT e.id_equipo, e.nombre AS equipo,
               COALESCE(SUM(t.color = 'amarilla'), 0) AS amarillas,
               COALESCE(SUM(t.color = 'roja'), 0)     AS rojas,
               COALESCE(SUM(CASE t.color WHEN 'amarilla' THEN 1 WHEN 'roja' THEN 3 END), 0) AS puntaje
        FROM equipo e
        LEFT JOIN planilla_partido pp ON pp.id_equipo = e.id_equipo
        LEFT JOIN tarjeta t ON t.id_partido = pp.id_partido AND t.ci_jugador = pp.ci_jugador
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo, e.nombre
        ORDER BY puntaje ASC, e.nombre
    """, (id_torneo,)))


@bp.get("/promedio-goles")
@cualquier_rol
def promedio_goles():
    id_torneo = param_entero("id_torneo")
    por_fecha = query(f"""
        SELECT numero_fecha,
               COUNT(*)                                     AS partidos,
               SUM(goles_local + goles_visitante)           AS goles,
               ROUND(AVG(goles_local + goles_visitante), 2) AS promedio
        FROM ({RESULTADOS}) r
        WHERE id_torneo = %s
        GROUP BY numero_fecha
        ORDER BY numero_fecha
    """, (id_torneo,))
    edicion = query(f"""
        SELECT COUNT(*)                                        AS partidos,
               COALESCE(SUM(goles_local + goles_visitante), 0) AS goles,
               ROUND(AVG(goles_local + goles_visitante), 2)    AS promedio
        FROM ({RESULTADOS}) r
        WHERE id_torneo = %s
    """, (id_torneo,), one=True)
    return jsonify(por_fecha=por_fecha, edicion=edicion)


@bp.get("/canchas")
@cualquier_rol
def canchas_mas_usadas():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT co.id_complejo, co.nombre AS complejo, p.nombre_cancha, COUNT(*) AS partidos
        FROM partido p
        JOIN complejo co ON co.id_complejo = p.id_complejo
        WHERE p.id_torneo = %s AND p.estado IN ('programado', 'jugado')
        GROUP BY co.id_complejo, co.nombre, p.nombre_cancha
        ORDER BY partidos DESC, co.nombre, p.nombre_cancha
    """, (id_torneo,)))


@bp.get("/turnos")
@cualquier_rol
def turnos_mas_usados():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT t.id_turno, t.hora_inicio, t.hora_fin, COUNT(p.id_partido) AS partidos
        FROM turno t
        LEFT JOIN partido p ON p.id_turno = t.id_turno
                           AND p.id_torneo = %s
                           AND p.estado IN ('programado', 'jugado')
        GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
        ORDER BY partidos DESC, t.hora_inicio
    """, (id_torneo,)))


@bp.get("/jugadores-por-facultad")
@cualquier_rol
def jugadores_por_facultad():
    """Sin id_torneo cuenta todos los jugadores; con id_torneo, solo los inscriptos en esa edición."""
    id_torneo = param_entero("id_torneo", requerido=False)
    filtro, params = "", ()
    if id_torneo is not None:
        filtro = "JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = j.ci AND ejt.id_torneo = %s"
        params = (id_torneo,)
    return jsonify(query(f"""
        SELECT f.nombre AS facultad, j.tipo, COUNT(*) AS cantidad
        FROM jugador j
        JOIN facultad f ON f.id_facultad = j.id_facultad
        {filtro}
        GROUP BY f.nombre, j.tipo
        ORDER BY f.nombre, j.tipo
    """, params))


@bp.get("/jugadores-sin-jugar")
@cualquier_rol
def jugadores_sin_jugar():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo
        FROM equipo_jugador_torneo ejt
        JOIN jugador j ON j.ci = ejt.ci_jugador
        JOIN equipo e  ON e.id_equipo = ejt.id_equipo
        WHERE ejt.id_torneo = %s
          AND NOT EXISTS (
              SELECT 1
              FROM planilla_partido pp
              JOIN partido p ON p.id_partido = pp.id_partido
              WHERE pp.ci_jugador = ejt.ci_jugador AND p.id_torneo = ejt.id_torneo
          )
        ORDER BY e.nombre, j.apellido
    """, (id_torneo,)))


@bp.get("/sanciones")
@cualquier_rol
def sanciones_por_equipo():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT e.nombre AS equipo, s.motivo, COUNT(*) AS cantidad
        FROM sancion_jugador s
        JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador
                                      AND ejt.id_torneo  = s.id_torneo
        JOIN equipo e ON e.id_equipo = ejt.id_equipo
        WHERE s.id_torneo = %s
        GROUP BY e.nombre, s.motivo
        ORDER BY e.nombre, s.motivo
    """, (id_torneo,)))


@bp.get("/estado-partidos")
@cualquier_rol
def estado_partidos():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT estado,
               COUNT(*) AS cantidad,
               ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS porcentaje
        FROM partido
        WHERE id_torneo = %s
        GROUP BY estado
        ORDER BY cantidad DESC
    """, (id_torneo,)))


# ---------- Consultas propuestas por el grupo ----------

@bp.get("/suspendidos")
@cualquier_rol
def suspendidos():
    """Jugadores que no pueden jugar en una fecha (?id_torneo=N&numero_fecha=M)."""
    id_torneo = param_entero("id_torneo")
    numero_fecha = param_entero("numero_fecha")
    return jsonify(query("""
        SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, s.motivo,
               s.numero_fecha_inicio AS desde,
               s.numero_fecha_inicio + s.cantidad_fechas - 1 AS hasta
        FROM sancion_jugador s
        JOIN jugador j ON j.ci = s.ci_jugador
        JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
        JOIN equipo e ON e.id_equipo = ejt.id_equipo
        WHERE s.id_torneo = %s
          AND %s BETWEEN s.numero_fecha_inicio AND s.numero_fecha_inicio + s.cantidad_fechas - 1
        ORDER BY e.nombre, j.apellido
    """, (id_torneo, numero_fecha)))


@bp.get("/goles-por-tramo")
@cualquier_rol
def goles_por_tramo():
    id_torneo = param_entero("id_torneo")
    # El tramo se calcula en una subconsulta para cumplir ONLY_FULL_GROUP_BY
    return jsonify(query("""
        SELECT CONCAT(x.tramo * 10, '-', x.tramo * 10 + 9) AS tramo, COUNT(*) AS goles
        FROM (
            SELECT FLOOR(g.minuto / 10) AS tramo
            FROM gol g
            JOIN partido p ON p.id_partido = g.id_partido
            WHERE p.id_torneo = %s AND p.estado = 'jugado'
        ) x
        GROUP BY x.tramo
        ORDER BY x.tramo
    """, (id_torneo,)))


@bp.get("/edad-promedio")
@cualquier_rol
def edad_promedio():
    id_torneo = param_entero("id_torneo")
    return jsonify(query("""
        SELECT e.nombre AS equipo,
               ROUND(AVG(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())), 1) AS edad_promedio,
               MIN(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())) AS mas_joven,
               MAX(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())) AS mas_grande
        FROM equipo e
        JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
        JOIN jugador j ON j.ci = ejt.ci_jugador
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo, e.nombre
        ORDER BY edad_promedio
    """, (id_torneo,)))
