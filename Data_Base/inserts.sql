use torneofut5;
 INSERT INTO turno (hora_inicio, hora_fin) VALUES
('18:00:00','19:00:00'),
('19:00:00','20:00:00'),
('20:00:00','21:00:00'),
('21:00:00','22:00:00'),
('22:00:00','23:00:00');



-- 1. TABLAS BASE
INSERT INTO login (correo, password, rol) VALUES
('admin@ucu.edu.uy',     '$2b$12$REEMPLAZAR_POR_HASH_BCRYPT', 'administrador'),
('planillero@ucu.edu.uy','$2b$12$REEMPLAZAR_POR_HASH_BCRYPT', 'planillero');

INSERT INTO facultad (id_facultad, nombre) VALUES
(1, 'Ingeniería y Tecnologías'),
(2, 'Derecho'),
(3, 'Ciencias Empresariales'),
(4, 'Psicología'),
(5, 'Comunicación');

INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
(1, 'Torneo Interfacultades 2026-2', 2026, 2, '2026-10-05', '2026-12-18', 'en curso');

INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
(1, 'Complejo Deportivo Campus', 'Av. 8 de Octubre 2738',  'Montevideo'),
(2, 'Fútbol 5 Pocitos',          'Bulevar España 2150',     'Montevideo');

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha 1', 1, 'sintetico', FALSE),
('Cancha 2', 1, 'sintetico', TRUE),
('Cancha 1', 2, 'parquet',   TRUE);

-- 2. JUGADORES (4 equipos x 6
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
-- Ingenieria (facultad 1)
(4000001, 'Martín',   'Pereira',  'martin.pereira@ucu.edu.uy',   '2003-02-14', 1, 'grado'),
(4000002, 'Lucas',    'Techera',  'lucas.techera@ucu.edu.uy',    '2002-07-30', 1, 'grado'),
(4000003, 'Diego',    'Rodríguez','diego.rodriguez@ucu.edu.uy',  '2001-11-05', 1, 'grado'),
(4000004, 'Santiago', 'Fagúndez', 'santiago.fagundez@ucu.edu.uy','1998-04-22', 1, 'posgrado'),
(4000005, 'Andrés',   'Mazzini',  'andres.mazzini@ucu.edu.uy',   '1985-09-10', 1, 'docente'),
(4000006, 'Joaquín',  'Silva',    'joaquin.silva@ucu.edu.uy',    '2004-01-18', 1, 'grado'),
-- Derecho (facultad 2)
(4100001, 'Nicolás',  'Acosta',   'nicolas.acosta@ucu.edu.uy',   '2002-03-09', 2, 'grado'),
(4100002, 'Facundo',  'Benítez',  'facundo.benitez@ucu.edu.uy',  '2003-06-25', 2, 'grado'),
(4100003, 'Mateo',    'Cabrera',  'mateo.cabrera@ucu.edu.uy',    '2001-12-01', 2, 'grado'),
(4100004, 'Bruno',    'Delgado',  'bruno.delgado@ucu.edu.uy',    '2002-08-17', 2, 'grado'),
(4100005, 'Ricardo',  'Estévez',  'ricardo.estevez@ucu.edu.uy',  '1980-05-12', 2, 'funcionario'),
(4100006, 'Tomás',    'Ferreira', 'tomas.ferreira@ucu.edu.uy',   '1997-10-03', 2, 'posgrado'),
-- Ciencias Empresariales (facultad 3)
(4200001, 'Agustín',  'Gómez',    'agustin.gomez@ucu.edu.uy',    '2003-01-27', 3, 'grado'),
(4200002, 'Emiliano', 'Herrera',  'emiliano.herrera@ucu.edu.uy', '2002-09-14', 3, 'grado'),
(4200003, 'Franco',   'Iglesias', 'franco.iglesias@ucu.edu.uy',  '2001-05-20', 3, 'grado'),
(4200004, 'Gonzalo',  'Juárez',   'gonzalo.juarez@ucu.edu.uy',   '1996-02-08', 3, 'posgrado'),
(4200005, 'Ignacio',  'Long',     'ignacio.long@ucu.edu.uy',     '2004-07-11', 3, 'grado'),
(4200006, 'Marcelo',  'Mendoza',  'marcelo.mendoza@ucu.edu.uy',  '1978-12-30', 3, 'docente'),
-- Psicología (facultad 4)
(4300001, 'Pablo',    'Núñez',    'pablo.nunez@ucu.edu.uy',      '2002-04-04', 4, 'grado'),
(4300002, 'Rodrigo',  'Olivera',  'rodrigo.olivera@ucu.edu.uy',  '2003-10-19', 4, 'grado'),
(4300003, 'Sebastián','Píriz',    'sebastian.piriz@ucu.edu.uy',  '2001-08-23', 4, 'grado'),
(4300004, 'Valentín', 'Quiroga',  'valentin.quiroga@ucu.edu.uy', '2002-11-29', 4, 'grado'),
(4300005, 'Walter',   'Rivero',   'walter.rivero@ucu.edu.uy',    '1983-03-15', 4, 'funcionario'),
(4300006, 'Héctor',   'Suárez',   'hector.suarez@ucu.edu.uy',    '1979-06-07', 4, 'docente'),
-- Sin inscribir en ningún equipo (Comunicación)
(4400001, 'Camila',   'Techera',  'camila.techera@ucu.edu.uy',   '2003-05-05', 5, 'grado'),
(4400002, 'Leonardo', 'Umpiérrez','leonardo.umpierrez@ucu.edu.uy','1981-09-21', 5, 'docente');

-- 3. EQUIPOS Y PLANTELES
-- El capitan se asigna despues, cuando ya existe el plantel
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
(1, 'Ingeniería FC',        1, 1, NULL),
(2, 'Los Abogados',         1, 2, NULL),
(3, 'Empresariales United', 1, 3, NULL),
(4, 'Psico Sport',          1, 4, NULL);

INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(1, 4000001, 1, 1), (1, 4000002, 1, 7), (1, 4000003, 1, 9),
(1, 4000004, 1, 5), (1, 4000005, 1, 4), (1, 4000006, 1, 11),
(2, 4100001, 1, 10),(2, 4100002, 1, 7), (2, 4100003, 1, 9),
(2, 4100004, 1, 5), (2, 4100005, 1, 3), (2, 4100006, 1, 1),
(3, 4200001, 1, 10),(3, 4200002, 1, 8), (3, 4200003, 1, 9),
(3, 4200004, 1, 4), (3, 4200005, 1, 2), (3, 4200006, 1, 1),
(4, 4300001, 1, 10),(4, 4300002, 1, 7), (4, 4300003, 1, 6),
(4, 4300004, 1, 5), (4, 4300005, 1, 3), (4, 4300006, 1, 1);

UPDATE equipo SET ci_capitan = 4000001 WHERE id_equipo = 1;
UPDATE equipo SET ci_capitan = 4100001 WHERE id_equipo = 2;
UPDATE equipo SET ci_capitan = 4200001 WHERE id_equipo = 3;
UPDATE equipo SET ci_capitan = 4300001 WHERE id_equipo = 4;

-- 4. PARTIDOS
-- turno 1 = 18-19, turno 2 = 19-20, turno 3 = 20-21, turno 4 = 21-22
INSERT INTO partido
(id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
 dia, id_turno, nombre_cancha, id_complejo, estado, fecha_jugado) VALUES
-- Fecha 1
(1, 1, 1, 1, 2, '2026-10-05', 1, 'Cancha 1', 1, 'jugado',     '2026-10-05 19:00:00'),
(2, 1, 1, 3, 4, '2026-10-05', 1, 'Cancha 2', 1, 'jugado',     '2026-10-05 19:00:00'),
-- Fecha 2
(3, 1, 2, 1, 3, '2026-10-12', 2, 'Cancha 1', 1, 'jugado',     '2026-10-12 20:00:00'),
(4, 1, 2, 2, 4, '2026-10-12', 2, 'Cancha 1', 2, 'jugado',     '2026-10-12 20:00:00'),
-- Fecha 3
(5, 1, 3, 1, 4, '2026-10-19', 3, 'Cancha 1', 1, 'cancelado',  NULL),
(6, 1, 3, 2, 3, '2026-10-19', 3, 'Cancha 1', 2, 'jugado',     '2026-10-19 21:00:00'),
-- Fecha 4: reprogramación del partido cancelado (se permite porque el anterior está cancelado)
(7, 1, 4, 1, 4, '2026-11-09', 4, 'Cancha 2', 1, 'programado', NULL);

-- 5. PLANILLAS (5 jugadores por equipo)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
-- Partido 1: Ingeniería vs Derecho
(1, 4000001, 1), (1, 4000002, 1), (1, 4000003, 1), (1, 4000004, 1), (1, 4000005, 1),
(1, 4100001, 2), (1, 4100002, 2), (1, 4100003, 2), (1, 4100004, 2), (1, 4100005, 2),
-- Partido 2: Empresariales vs Psicología
(2, 4200001, 3), (2, 4200002, 3), (2, 4200003, 3), (2, 4200004, 3), (2, 4200005, 3),
(2, 4300001, 4), (2, 4300002, 4), (2, 4300003, 4), (2, 4300004, 4), (2, 4300005, 4),
-- Partido 3: Ingeniería vs Empresariales (sin 4000003, suspendido)
(3, 4000001, 1), (3, 4000002, 1), (3, 4000004, 1), (3, 4000005, 1), (3, 4000006, 1),
(3, 4200001, 3), (3, 4200002, 3), (3, 4200003, 3), (3, 4200004, 3), (3, 4200005, 3),
-- Partido 4: Derecho vs Psicología
(4, 4100001, 2), (4, 4100002, 2), (4, 4100003, 2), (4, 4100004, 2), (4, 4100005, 2),
(4, 4300001, 4), (4, 4300002, 4), (4, 4300003, 4), (4, 4300004, 4), (4, 4300005, 4),
-- Partido 6: Derecho vs Empresariales
(6, 4100001, 2), (6, 4100002, 2), (6, 4100003, 2), (6, 4100004, 2), (6, 4100005, 2),
(6, 4200001, 3), (6, 4200002, 3), (6, 4200003, 3), (6, 4200004, 3), (6, 4200005, 3);

-- 6. GOLES
-- Resultados: P1 2-1 | P2 1-1 | P3 2-0 (incluye autogol) | P4 3-2 | P6 1-1
INSERT INTO gol (id_gol, id_partido, ci_jugador, minuto, autogol) VALUES
-- P1: Ingeniería 2 - 1 Derecho
(1,  1, 4000001, 12, FALSE),
(2,  1, 4000002, 33, FALSE),
(3,  1, 4100001, 40, FALSE),
-- P2: Empresariales 1 - 1 Psicología
(4,  2, 4200001, 20, FALSE),
(5,  2, 4300001, 48, FALSE),
-- P3: Ingenieria 0 - 2 Empresariales (el segundo es autogol de 4000004)
(6,  3, 4200001, 10, FALSE),
(7,  3, 4000004, 55, TRUE),
-- P4: Derecho 3 - 2 Psicología
(8,  4, 4100001,  5, FALSE),
(9,  4, 4100003, 18, FALSE),
(10, 4, 4300002, 30, FALSE),
(11, 4, 4100001, 44, FALSE),
(12, 4, 4300001, 52, FALSE),
-- P6: Derecho 1 - 1 Empresariales
(13, 6, 4100002, 29, FALSE),
(14, 6, 4200003, 38, FALSE);

-- 7. TARJETAS
INSERT INTO tarjeta (id_tarjeta, id_partido, ci_jugador, minuto, color) VALUES
(1, 1, 4000003, 50, 'roja'),       -- origina sanción de 1 fecha
(2, 1, 4100002, 25, 'amarilla'),
(3, 2, 4200002, 22, 'amarilla'),   -- 1ª amarilla de 4200002
(4, 2, 4300003, 30, 'amarilla'),
(5, 3, 4200002, 41, 'amarilla'),   -- 2ª amarilla de 4200002
(6, 4, 4100004, 37, 'amarilla'),
(7, 6, 4200002, 15, 'amarilla');   -- 3ª amarilla de 4200002 -> sanción

-- 8. SANCIONES
INSERT INTO sancion_jugador
(id_sancion, ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, id_tarjeta_origen) VALUES
-- Roja en fecha 1 -> suspendido en fecha 2
(1, 4000003, 1, 'roja', 2, 1, 1),
-- 3 amarillas (última en fecha 3) -> suspendido en fecha 4
(2, 4200002, 1, 'acumulacion de amarillas', 4, 1, 7),
-- Disciplinaria cargada por la organización: fechas 3 y 4
(3, 4300004, 1, 'disciplinaria', 3, 2, NULL);