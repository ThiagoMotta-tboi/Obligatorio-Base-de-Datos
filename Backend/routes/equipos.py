from flask import Blueprint, jsonify

from auth import cualquier_rol, solo_admin
from db import query, transaccion, uno, uno_o_404
from utils import ErrorNegocio, datos_json, entero, param_entero, requeridos

bp = Blueprint("equipos", __name__, url_prefix="/api/equipos")

MAX_JUGADORES = 10
MAX_DOCENTES_FUNCIONARIOS = 2


def _equipo_en_inscripcion(cur, id_equipo):
    """Devuelve el equipo y verifica que su torneo permita modificar planteles."""
    equipo = uno_o_404(cur, """
        SELECT e.id_equipo, e.nombre, e.id_torneo, e.id_facultad, e.ci_capitan, t.estado
        FROM equipo e
        JOIN torneo t ON t.id_torneo = e.id_torneo
        WHERE e.id_equipo = %s
    """, (id_equipo,), "Equipo no encontrado")
    if equipo["estado"] != "inscripcion":
        raise ErrorNegocio("Los planteles solo pueden modificarse con el torneo en etapa de inscripción", 409)
    return equipo


def _validar_camiseta(cur, id_equipo, numero, ci_excluido=None):
    numero = entero(numero, "numero_camiseta", minimo=1, maximo=99)
    ocupada = uno(cur, """
        SELECT ci_jugador FROM equipo_jugador_torneo
        WHERE id_equipo = %s AND numero_camiseta = %s AND ci_jugador <> %s
    """, (id_equipo, numero, ci_excluido or 0))
    if ocupada:
        raise ErrorNegocio(f"La camiseta {numero} ya la usa otro jugador del equipo", 409)
    return numero


def _validar_capitan(cur, id_equipo, ci_capitan):
    if ci_capitan is None:
        return None
    ci_capitan = entero(ci_capitan, "ci_capitan")
    if not uno(cur, "SELECT 1 FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s",
               (id_equipo, ci_capitan)):
        raise ErrorNegocio("El capitán debe ser un jugador del plantel del equipo")
    return ci_capitan


# ---------- Equipos ----------

@bp.get("")
@cualquier_rol
def listar():
    id_torneo = param_entero("id_torneo", requerido=False)
    where = "WHERE e.id_torneo = %s" if id_torneo is not None else ""
    params = (id_torneo,) if id_torneo is not None else ()
    return jsonify(query(f"""
        SELECT e.id_equipo, e.nombre, e.id_torneo, t.nombre AS torneo,
               e.id_facultad, f.nombre AS facultad,
               e.ci_capitan, CONCAT(c.nombre, ' ', c.apellido) AS capitan,
               COUNT(ejt.ci_jugador) AS jugadores
        FROM equipo e
        JOIN torneo t   ON t.id_torneo = e.id_torneo
        JOIN facultad f ON f.id_facultad = e.id_facultad
        LEFT JOIN jugador c ON c.ci = e.ci_capitan
        LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
        {where}
        GROUP BY e.id_equipo, e.nombre, e.id_torneo, t.nombre, e.id_facultad, f.nombre,
                 e.ci_capitan, c.nombre, c.apellido
        ORDER BY e.nombre
    """, params))


@bp.get("/<int:id_equipo>")
@cualquier_rol
def obtener(id_equipo):
    equipo = query("""
        SELECT e.id_equipo, e.nombre, e.id_torneo, t.nombre AS torneo, t.estado AS estado_torneo,
               e.id_facultad, f.nombre AS facultad, e.ci_capitan
        FROM equipo e
        JOIN torneo t   ON t.id_torneo = e.id_torneo
        JOIN facultad f ON f.id_facultad = e.id_facultad
        WHERE e.id_equipo = %s
    """, (id_equipo,), one=True)
    if not equipo:
        raise ErrorNegocio("Equipo no encontrado", 404)
    equipo["plantel"] = _plantel(id_equipo)
    return jsonify(equipo)


@bp.post("")
@solo_admin
def crear():
    datos = datos_json()
    requeridos(datos, ["nombre", "id_torneo", "id_facultad"])
    id_torneo = entero(datos["id_torneo"], "id_torneo")
    id_facultad = entero(datos["id_facultad"], "id_facultad")

    with transaccion() as cur:
        torneo = uno_o_404(cur, "SELECT estado FROM torneo WHERE id_torneo = %s",
                           (id_torneo,), "Torneo no encontrado")
        if torneo["estado"] != "inscripcion":
            raise ErrorNegocio("Solo se pueden inscribir equipos con el torneo en etapa de inscripción", 409)
        cur.execute("""
            INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s, %s, %s)
        """, (datos["nombre"], id_torneo, id_facultad))
        id_equipo = cur.lastrowid
    return jsonify(mensaje="Equipo creado. Cargue el plantel y luego asigne el capitán",
                   id_equipo=id_equipo), 201


@bp.put("/<int:id_equipo>")
@solo_admin
def modificar(id_equipo):
    """Modifica nombre y capitán. La facultad solo cambia si el plantel está vacío."""
    datos = datos_json()
    requeridos(datos, ["nombre"])

    with transaccion() as cur:
        equipo = uno_o_404(cur, """
            SELECT e.id_facultad, e.ci_capitan, t.estado,
                   (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                    WHERE ejt.id_equipo = e.id_equipo) AS jugadores
            FROM equipo e JOIN torneo t ON t.id_torneo = e.id_torneo
            WHERE e.id_equipo = %s
        """, (id_equipo,), "Equipo no encontrado")

        id_facultad = entero(datos.get("id_facultad", equipo["id_facultad"]), "id_facultad")
        if id_facultad != equipo["id_facultad"]:
            if equipo["estado"] != "inscripcion" or equipo["jugadores"] > 0:
                raise ErrorNegocio("La facultad solo puede cambiarse en inscripción y con el plantel vacío", 409)

        # Si no se envía ci_capitan se mantiene el actual
        ci_capitan = _validar_capitan(cur, id_equipo, datos.get("ci_capitan", equipo["ci_capitan"]))
        cur.execute("""
            UPDATE equipo SET nombre = %s, id_facultad = %s, ci_capitan = %s
            WHERE id_equipo = %s
        """, (datos["nombre"], id_facultad, ci_capitan, id_equipo))
    return jsonify(mensaje="Equipo modificado")


@bp.delete("/<int:id_equipo>")
@solo_admin
def eliminar(id_equipo):
    with transaccion() as cur:
        _equipo_en_inscripcion(cur, id_equipo)
        if uno(cur, """
            SELECT 1 FROM partido WHERE id_equipo_local = %s OR id_equipo_visitante = %s LIMIT 1
        """, (id_equipo, id_equipo)):
            raise ErrorNegocio("El equipo tiene partidos asignados; elimínelos primero", 409)
        # El capitán referencia al plantel, así que se libera antes de borrarlo
        cur.execute("UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s", (id_equipo,))
        cur.execute("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_equipo,))
        cur.execute("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,))
    return jsonify(mensaje="Equipo eliminado")


# ---------- Plantel ----------

def _plantel(id_equipo):
    return query("""
        SELECT ejt.numero_camiseta, j.ci, j.nombre, j.apellido, j.tipo,
               (j.ci = e.ci_capitan) AS es_capitan
        FROM equipo_jugador_torneo ejt
        JOIN jugador j ON j.ci = ejt.ci_jugador
        JOIN equipo e  ON e.id_equipo = ejt.id_equipo
        WHERE ejt.id_equipo = %s
        ORDER BY ejt.numero_camiseta
    """, (id_equipo,))


@bp.get("/<int:id_equipo>/jugadores")
@cualquier_rol
def listar_plantel(id_equipo):
    if not query("SELECT 1 FROM equipo WHERE id_equipo = %s", (id_equipo,), one=True):
        raise ErrorNegocio("Equipo no encontrado", 404)
    return jsonify(_plantel(id_equipo))


@bp.get("/<int:id_equipo>/disponibles")
@solo_admin
def jugadores_disponibles(id_equipo):
    """Jugadores de la facultad del equipo que todavía no tienen equipo en esa edición."""
    if not query("SELECT 1 FROM equipo WHERE id_equipo = %s", (id_equipo,), one=True):
        raise ErrorNegocio("Equipo no encontrado", 404)
    return jsonify(query("""
        SELECT j.ci, j.nombre, j.apellido, j.tipo
        FROM jugador j
        JOIN equipo e ON e.id_equipo = %s
        WHERE j.id_facultad = e.id_facultad
          AND NOT EXISTS (
              SELECT 1 FROM equipo_jugador_torneo ejt
              WHERE ejt.ci_jugador = j.ci AND ejt.id_torneo = e.id_torneo
          )
        ORDER BY j.apellido, j.nombre
    """, (id_equipo,)))


@bp.post("/<int:id_equipo>/jugadores")
@solo_admin
def agregar_jugador(id_equipo):
    datos = datos_json()
    requeridos(datos, ["ci_jugador", "numero_camiseta"])
    ci = entero(datos["ci_jugador"], "ci_jugador")

    with transaccion() as cur:
        equipo = _equipo_en_inscripcion(cur, id_equipo)
        jugador = uno_o_404(cur, "SELECT ci, id_facultad, tipo FROM jugador WHERE ci = %s",
                            (ci,), "Jugador no encontrado")

        if jugador["id_facultad"] != equipo["id_facultad"]:
            raise ErrorNegocio("El jugador no pertenece a la facultad que representa el equipo")

        otro = uno(cur, """
            SELECT e.nombre FROM equipo_jugador_torneo ejt
            JOIN equipo e ON e.id_equipo = ejt.id_equipo
            WHERE ejt.ci_jugador = %s AND ejt.id_torneo = %s
        """, (ci, equipo["id_torneo"]))
        if otro:
            raise ErrorNegocio(f"El jugador ya integra el equipo '{otro['nombre']}' en esta edición", 409)

        conteo = uno(cur, """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(j.tipo IN ('docente', 'funcionario')), 0) AS docentes_funcionarios
            FROM equipo_jugador_torneo ejt
            JOIN jugador j ON j.ci = ejt.ci_jugador
            WHERE ejt.id_equipo = %s
        """, (id_equipo,))
        if conteo["total"] >= MAX_JUGADORES:
            raise ErrorNegocio(f"El plantel ya tiene el máximo de {MAX_JUGADORES} jugadores", 409)
        if (jugador["tipo"] in ("docente", "funcionario")
                and conteo["docentes_funcionarios"] >= MAX_DOCENTES_FUNCIONARIOS):
            raise ErrorNegocio(
                f"El plantel ya tiene {MAX_DOCENTES_FUNCIONARIOS} docentes/funcionarios (máximo permitido)", 409)

        numero = _validar_camiseta(cur, id_equipo, datos["numero_camiseta"])
        cur.execute("""
            INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
            VALUES (%s, %s, %s, %s)
        """, (id_equipo, ci, equipo["id_torneo"], numero))
    return jsonify(mensaje="Jugador agregado al plantel"), 201


@bp.put("/<int:id_equipo>/jugadores/<int:ci>")
@solo_admin
def modificar_camiseta(id_equipo, ci):
    datos = datos_json()
    requeridos(datos, ["numero_camiseta"])
    with transaccion() as cur:
        _equipo_en_inscripcion(cur, id_equipo)
        uno_o_404(cur, "SELECT 1 FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s",
                  (id_equipo, ci), "El jugador no está en el plantel")
        numero = _validar_camiseta(cur, id_equipo, datos["numero_camiseta"], ci_excluido=ci)
        cur.execute("""
            UPDATE equipo_jugador_torneo SET numero_camiseta = %s
            WHERE id_equipo = %s AND ci_jugador = %s
        """, (numero, id_equipo, ci))
    return jsonify(mensaje="Número de camiseta modificado")


@bp.delete("/<int:id_equipo>/jugadores/<int:ci>")
@solo_admin
def quitar_jugador(id_equipo, ci):
    with transaccion() as cur:
        equipo = _equipo_en_inscripcion(cur, id_equipo)
        uno_o_404(cur, "SELECT 1 FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s",
                  (id_equipo, ci), "El jugador no está en el plantel")
        if equipo["ci_capitan"] == ci:
            raise ErrorNegocio("El jugador es el capitán; asigne otro capitán antes de quitarlo", 409)
        cur.execute("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s",
                    (id_equipo, ci))
    return jsonify(mensaje="Jugador quitado del plantel")
