"""Fragmentos SQL que usan varios módulos."""

# Resultado de cada partido jugado, calculado a partir de los goles.
# Un gol suma para el equipo del jugador según la planilla; un autogol suma para el rival.
RESULTADOS = """
    SELECT p.id_partido, p.id_torneo, p.numero_fecha,
           p.id_equipo_local, p.id_equipo_visitante,
           COALESCE(SUM((pp.id_equipo = p.id_equipo_local)     XOR g.autogol), 0) AS goles_local,
           COALESCE(SUM((pp.id_equipo = p.id_equipo_visitante) XOR g.autogol), 0) AS goles_visitante
    FROM partido p
    LEFT JOIN gol g ON g.id_partido = p.id_partido
    LEFT JOIN planilla_partido pp ON pp.id_partido = g.id_partido
                                 AND pp.ci_jugador = g.ci_jugador
    WHERE p.estado = 'jugado'
    GROUP BY p.id_partido
"""

# Sanción vigente de un jugador en una fecha. Parámetros: ci, id_torneo, numero_fecha.
SANCION_VIGENTE = """
    SELECT id_sancion, motivo, numero_fecha_inicio,
           numero_fecha_inicio + cantidad_fechas - 1 AS numero_fecha_fin
    FROM sancion_jugador
    WHERE ci_jugador = %s
      AND id_torneo = %s
      AND %s BETWEEN numero_fecha_inicio AND numero_fecha_inicio + cantidad_fechas - 1
"""
