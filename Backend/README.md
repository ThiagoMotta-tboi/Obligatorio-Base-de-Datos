# Backend – Torneo Interfacultades de Fútbol 5

API REST en Python + Flask. Las consultas son SQL escrito a mano (`mysql-connector-python`, sin ORM)
y siempre con parámetros `%s`, nunca concatenando valores.

## Puesta en marcha

1. Crear la base con `Data_Base/Create_Tables.sql` y cargar `Data_Base/inserts.sql`.
2. Desde la carpeta `Backend`:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # y completar DB_PASSWORD y JWT_SECRET_KEY
```

3. Crear los usuarios con contraseña hasheada (reemplaza los hashes de relleno de los inserts):

```powershell
python crear_usuario.py admin@ucu.edu.uy admin123 administrador
python crear_usuario.py planillero@ucu.edu.uy plani123 planillero
```

4. Levantar la API en `http://localhost:5000`:

```powershell
python app.py
```

`GET /api/salud` confirma que la conexión a la base funciona.

## Autenticación

`POST /api/auth/login` con `{"correo": "...", "password": "..."}` devuelve un `token`.
El resto de los endpoints requiere el header `Authorization: Bearer <token>`.

- **administrador**: gestiona todo.
- **planillero**: consulta datos y carga planillas, goles y tarjetas; también puede marcar un partido como jugado.

## Estructura

| Archivo | Contenido |
|---|---|
| `app.py` | Arranque, registro de rutas y manejo de errores (incluye errores de MySQL) |
| `db.py` | Conexión, `query`, `execute` y `transaccion()` para operaciones de varios pasos |
| `auth.py` | Decoradores de roles (`solo_admin`, `cualquier_rol`) |
| `utils.py` | Validación de datos de entrada y `ErrorNegocio` |
| `sql_comun.py` | SQL compartido: resultado de los partidos y sanción vigente |
| `routes/` | Un módulo por entidad |

## Endpoints

| Recurso | Endpoints |
|---|---|
| Facultades | `GET/POST /api/facultades`, `GET/PUT/DELETE /api/facultades/<id>` |
| Jugadores | `GET/POST /api/jugadores` (filtros `id_facultad`, `tipo`), `GET/PUT/DELETE /api/jugadores/<ci>` |
| Torneos | `GET/POST /api/torneos`, `GET/PUT/DELETE /api/torneos/<id>`, `PUT /api/torneos/<id>/estado` |
| Complejos | `GET/POST /api/complejos`, `GET/PUT/DELETE /api/complejos/<id>` |
| Canchas | `GET /api/canchas`, `POST /api/complejos/<id>/canchas`, `PUT/DELETE /api/complejos/<id>/canchas/<nombre>` |
| Turnos | `GET /api/turnos` |
| Equipos | `GET/POST /api/equipos` (filtro `id_torneo`), `GET/PUT/DELETE /api/equipos/<id>` |
| Planteles | `GET/POST /api/equipos/<id>/jugadores`, `PUT/DELETE /api/equipos/<id>/jugadores/<ci>`, `GET /api/equipos/<id>/disponibles` |
| Partidos | `GET/POST /api/partidos` (filtros `id_torneo`, `numero_fecha`, `estado`, `pendientes=1`), `GET/PUT/DELETE /api/partidos/<id>`, `PUT /api/partidos/<id>/estado` |
| Planilla | `GET /api/partidos/<id>/jugadores`, `GET/POST /api/partidos/<id>/planilla`, `DELETE /api/partidos/<id>/planilla/<ci>` |
| Goles | `GET/POST /api/partidos/<id>/goles`, `PUT/DELETE /api/partidos/<id>/goles/<id_gol>` |
| Tarjetas | `GET/POST /api/partidos/<id>/tarjetas`, `DELETE /api/partidos/<id>/tarjetas/<id_tarjeta>` |
| Sanciones | `GET/POST /api/sanciones` (filtros `id_torneo`, `ci_jugador`, `numero_fecha`), `PUT/DELETE /api/sanciones/<id>` |
| Reportes | `GET /api/reportes/<nombre>?id_torneo=N` |

Reportes disponibles: `posiciones`, `goleadores`, `fair-play`, `promedio-goles`, `canchas`, `turnos`,
`jugadores-por-facultad`, `jugadores-sin-jugar`, `sanciones`, `estado-partidos`, y los propuestos
`suspendidos` (requiere `numero_fecha`), `goles-por-tramo` y `edad-promedio`.

## Reglas que controla el backend

**Planteles** (solo con el torneo en inscripción): misma facultad que el equipo, un equipo por jugador
y edición, máximo 10 jugadores, máximo 2 docentes/funcionarios, camiseta no repetida, el capitán
pertenece al plantel y no puede quitarse.

**Torneo**: las etapas avanzan inscripción → en curso → finalizado. Para comenzar, cada equipo
necesita entre 5 y 10 jugadores y capitán; para finalizar, no puede haber partidos pendientes.

**Partidos**: equipos de la misma edición con al menos 5 jugadores, no contra sí mismo, sin rival
repetido (salvo partido cancelado), un partido por equipo y fecha, cancha libre en ese día y turno,
día dentro del torneo. Solo se marca como jugado si su día y turno pasaron; un jugado no se elimina.

**Planilla, goles y tarjetas**: solo jugadores del plantel de los dos equipos y no suspendidos;
goles y tarjetas solo de quienes figuran en la planilla; se carga con el partido ya disputado y,
si está jugado, solo dentro de las 48 horas siguientes.

**Sanciones automáticas**: una roja suspende la fecha siguiente; cada 3 amarillas en la edición,
también. Al borrar una tarjeta su sanción se recalcula.
