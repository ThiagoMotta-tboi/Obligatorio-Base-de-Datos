CREATE DATABASE IF NOT EXISTS torneofut5
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE torneofut5;

CREATE TABLE login (
    correo   VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,            -- guardar el hash, no texto plano
    rol      ENUM('administrador','planillero') NOT NULL
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE jugador (
    ci               INT PRIMARY KEY,
    nombre           VARCHAR(50)  NOT NULL,
    apellido         VARCHAR(50)  NOT NULL,
    email            VARCHAR(100) NOT NULL UNIQUE,
    fecha_nacimiento DATE         NOT NULL,
    id_facultad      INT          NOT NULL,
    tipo             ENUM('grado','posgrado','docente','funcionario') NOT NULL,
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
);

CREATE TABLE torneo (
    id_torneo    INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(50) NOT NULL,
    anio         INT NOT NULL,
    semestre     INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin    DATE NOT NULL,
    estado       ENUM('inscripcion','en curso','finalizado') NOT NULL DEFAULT 'inscripcion',
    UNIQUE (anio, semestre),
    CONSTRAINT chk_torneo_semestre CHECK (semestre IN (1,2)),
    CONSTRAINT chk_torneo_fechas   CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE equipo (
    id_equipo   INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL,
    id_torneo   INT NOT NULL,
    id_facultad INT NOT NULL,
    ci_capitan  INT NULL,                       -- se asigna cuando ya hay plantel
    UNIQUE (id_equipo, id_torneo),              -- necesario para las FK compuestas
    UNIQUE (nombre, id_torneo),
    FOREIGN KEY (id_torneo)   REFERENCES torneo(id_torneo),
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
);

CREATE TABLE equipo_jugador_torneo (
    id_equipo       INT NOT NULL,
    ci_jugador      INT NOT NULL,
    id_torneo       INT NOT NULL,
    numero_camiseta INT NOT NULL,
    PRIMARY KEY (ci_jugador, id_torneo),        -- un jugador, un solo equipo por edición
    UNIQUE (id_equipo, numero_camiseta),        -- camisetas no repetidas en el equipo
    CONSTRAINT chk_camiseta CHECK (numero_camiseta BETWEEN 1 AND 99),
    FOREIGN KEY (id_equipo, id_torneo) REFERENCES equipo(id_equipo, id_torneo),
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci)
);

-- Referencia circular: el capitán debe estar inscripto en el torneo del equipo
ALTER TABLE equipo
    ADD CONSTRAINT fk_equipo_capitan
    FOREIGN KEY (ci_capitan, id_torneo)
    REFERENCES equipo_jugador_torneo(ci_jugador, id_torneo);

CREATE TABLE complejo (
    id_complejo  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(50)  NOT NULL,
    direccion    VARCHAR(100) NOT NULL,
    departamento VARCHAR(50)  NOT NULL
);

CREATE TABLE cancha (
    nombre_cancha VARCHAR(100),
    id_complejo   INT,
    superficie    ENUM('sintetico','parquet') NOT NULL,
    techada       BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (nombre_cancha, id_complejo),
    FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE turno (
    id_turno    INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL UNIQUE,
    hora_fin    TIME NOT NULL,
    CONSTRAINT chk_turno_rango    CHECK (hora_inicio >= '18:00:00' AND hora_fin <= '23:00:00'),
    CONSTRAINT chk_turno_duracion CHECK (TIME_TO_SEC(hora_fin) - TIME_TO_SEC(hora_inicio) = 3600)
);

CREATE TABLE partido (
    id_partido          INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo           INT NOT NULL,
    numero_fecha        INT NOT NULL,
    id_equipo_local     INT NOT NULL,
    id_equipo_visitante INT NOT NULL,
    dia                 DATE NOT NULL,
    id_turno            INT NOT NULL,
    nombre_cancha       VARCHAR(100) NOT NULL,
    id_complejo         INT NOT NULL,
    estado              ENUM('programado','jugado','postergado','cancelado') NOT NULL DEFAULT 'programado',
    fecha_jugado        DATETIME NULL,          -- para controlar las 48 hs de corrección
    CONSTRAINT chk_partido_fecha   CHECK (numero_fecha > 0),
    CONSTRAINT chk_partido_rivales CHECK (id_equipo_local <> id_equipo_visitante),
    CONSTRAINT chk_partido_jugado  CHECK (estado <> 'jugado' OR fecha_jugado IS NOT NULL),
    FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
    FOREIGN KEY (id_equipo_local, id_torneo)     REFERENCES equipo(id_equipo, id_torneo),
    FOREIGN KEY (id_equipo_visitante, id_torneo) REFERENCES equipo(id_equipo, id_torneo),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    FOREIGN KEY (nombre_cancha, id_complejo) REFERENCES cancha(nombre_cancha, id_complejo)
);

CREATE TABLE planilla_partido (
    id_partido INT,
    ci_jugador INT,
    id_equipo  INT NOT NULL,
    PRIMARY KEY (id_partido, ci_jugador),
    FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    FOREIGN KEY (id_equipo)  REFERENCES equipo(id_equipo)
);

CREATE TABLE gol (
    id_gol     INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador INT NOT NULL,
    minuto     INT NOT NULL,
    autogol    BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_gol_minuto CHECK (minuto BETWEEN 0 AND 60),
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador)
);

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador INT NOT NULL,
    minuto     INT NOT NULL,
    color      ENUM('amarilla','roja') NOT NULL,
    CONSTRAINT chk_tarjeta_minuto CHECK (minuto BETWEEN 0 AND 60),
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador)
);

CREATE TABLE sancion_jugador (
    id_sancion          INT AUTO_INCREMENT PRIMARY KEY,
    ci_jugador          INT NOT NULL,
    id_torneo           INT NOT NULL,
    motivo              ENUM('roja','acumulacion de amarillas','disciplinaria') NOT NULL,
    numero_fecha_inicio INT NOT NULL,
    cantidad_fechas     INT NOT NULL,
    id_tarjeta_origen   INT NULL,               -- NULL en sanciones disciplinarias
    CONSTRAINT chk_sancion_inicio   CHECK (numero_fecha_inicio > 0),
    CONSTRAINT chk_sancion_cantidad CHECK (cantidad_fechas >= 1),
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    FOREIGN KEY (id_torneo)  REFERENCES torneo(id_torneo),
    FOREIGN KEY (id_tarjeta_origen) REFERENCES tarjeta(id_tarjeta) ON DELETE CASCADE
);