USE torneofut5;
SET @torneo = 1, @equipo = 1, @partido = 3, @ci = 4000003, @fecha = 2;

CREATE OR REPLACE VIEW v_resultado_partido AS
SELECT p.id_partido, p.id_torneo, p.numero_fecha,
       p.id_equipo_local, p.id_equipo_visitante,
       COALESCE(SUM(CASE WHEN (g.autogol = FALSE AND pp.id_equipo = p.id_equipo_local)
                           OR (g.autogol = TRUE  AND pp.id_equipo = p.id_equipo_visitante)
                         THEN 1 ELSE 0 END), 0) AS goles_local,
       COALESCE(SUM(CASE WHEN (g.autogol = FALSE AND pp.id_equipo = p.id_equipo_visitante)
                           OR (g.autogol = TRUE  AND pp.id_equipo = p.id_equipo_local)
                         THEN 1 ELSE 0 END), 0) AS goles_visitante
FROM partido p
LEFT JOIN gol g ON g.id_partido = p.id_partido
LEFT JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
WHERE p.estado = 'jugado'
GROUP BY p.id_partido, p.id_torneo, p.numero_fecha, p.id_equipo_local, p.id_equipo_visitante;

-- Tabla de Posiciones --
CREATE OR REPLACE VIEW tabla_pociciones AS
SELECT  e.nombre as equipo, COUNT(*) AS PJ, SUM(t.gf > t.gc) AS PG, SUM(t.gf = t.gc) AS PE, SUM(t.gf < t.gc) AS PP,
        SUM(t.gf) AS GF, SUM(t.gc) AS GC, SUM(t.gf - t.gc) AS DG,
        SUM(CASE WHEN t.gf > t.gc THEN 3 WHEN t.gf = t.gc THEN 1 ELSE 0 END)AS Pts
FROM (
     SELECT id_torneo, id_equipo_local AS id_equipo, goles_local AS gf, goles_visitante AS gc
    FROM v_resultado_partido
    UNION ALL
    SELECT id_torneo, id_equipo_visitante, goles_visitante, goles_local
    FROM v_resultado_partido
) t
JOIN equipo e on e.id_equipo = t.id_equipo
WHERE t.id_torneo =  @torneo
GROUP BY e.id_equipo , e.nombre
ORDER BY Pts desc, DG DESC , GF DESC;

-- Top 10 Goleadores --
CREATE OR REPLACE VIEW Goleadores AS
SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, COUNT(*) as goles
FROM gol g
join partido p on p.id_partido = g.id_partido
join planilla_partido pp on pp.id_partido = p.id_partido
join jugador j on j.ci = g.ci_jugador
join equipo e on e.id_equipo = pp.id_equipo
WHERE p.id_torneo = @torneo AND p.estado = 'jugado' AND g.autogol = FALSE
Group By  j.ci, j.nombre, j.apellido, e.nombre
Order by goles DESC, j.apellido
Limit 10;

-- Fair Play por Equipo --
CREATE OR REPLACE VIEW Fair_Play AS
SELECT e.nombre AS Equipo, Coalesce(SUM(t.color = 'amarilla'), 0 )AS amarillas, Coalesce(SUM(t.color = 'roja'),0) AS rojas, Coalesce(SUM(CASE t.color WHEN 'amarilla' THEN 1 WHEN 'roja' Then 3 END ), 0) AS Puntaje
FROM equipo e
LEFT JOIN planilla_partido pp On pp.id_equipo = e.id_equipo
LEFT JOIN tarjeta t on t.id_partido = pp.id_partido And t.ci_jugador = pp.ci_jugador
WHERE e.id_torneo = 1
Group By e.id_equipo, e.nombre
ORDER BY puntaje ASC ;

-- Promedio de goles por partido --
CREATE OR REPLACE VIEW Prom_golea_partido as
SELECT numero_fecha, COUNT(*) as partidos, Sum(goles_local + goles_visitante) as goles, ROUND(AVG(goles_local + goles_visitante), 2) AS promedio
From v_resultado_partido
WHERE id_torneo = @torneo
GROUP BY numero_fecha
order by  numero_fecha;

-- Canchas y turnos mas usados --

SELECT c.nombre AS complejo, p.nombre_cancha, Count(*) as Partidos
FROM partido p
Join complejo c on c.id_complejo = p.id_complejo
WHERE p.id_torneo = @torneo And p.estado In ('programado', 'jugado')
GROUP BY p.id_complejo, c.nombre, p.nombre_cancha
Order By Partidos DESC;

-- Jugadores por facultad y tipo --
SELECT  f.nombre AS Facultad, j.tipo, Count(*) as cantidad
From jugador j
Join facultad f on f.id_facultad = j.id_facultad
GROUP BY f.nombre, j.tipo;

-- Inscriptos que nunca Figuraron en una figuraron --
SELECT j.ci, j.nombre, j.apellido, e.nombre AS Equipo
From equipo_jugador_torneo ejt
JOIN jugador j on j.ci = ejt.ci_jugador
join equipo e on e.id_equipo = ejt.id_equipo
WHERE ejt.id_torneo = @torneo
    AND Not EXISTS(
        Select 1
        from planilla_partido pp
        join partido p on p.id_partido =pp.id_partido
        WHERE pp.ci_jugador = ejt.ci_jugador And p.id_torneo
);

-- Sanciones por equipo y su motivo --
SELECT  e.nombre as equipo, s.motivo, COUNT(*) as cantidad
FROM sancion_jugador s
JOIN equipo_jugador_torneo ejt on ejt.ci_jugador = s.ci_jugador and ejt.id_torneo = s.id_torneo
join equipo e on e.id_equipo = ejt.id_equipo
WHERE s.id_torneo =@torneo
GROUP BY e.nombre, s.motivo;

-- Porcentaje de partidos por estado--
SELECT estado, Count(*) as cantidad, Round(100 * COUNT(*) / SUM(Count(*)) Over (), 2) AS porcentaje
From partido
where id_torneo = @torneo
GROUP BY estado;

#Consultas realizadas por el equipo

-- Edad Promedio de los equipos --
SELECT e.nombre AS equipo,
       ROUND(AVG(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())), 1) AS edad_promedio,
       MIN(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())) AS mas_joven,
       MAX(TIMESTAMPDIFF(YEAR, j.fecha_nacimiento, CURDATE())) AS mas_grande
FROM equipo e
JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
JOIN jugador j ON j.ci = ejt.ci_jugador
WHERE e.id_torneo = 1
GROUP BY e.id_equipo, e.nombre
ORDER BY edad_promedio;
