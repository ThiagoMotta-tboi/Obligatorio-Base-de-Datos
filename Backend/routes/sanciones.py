from flask import Blueprint, jsonify

from auth import cualquier_rol, solo_admin
from db import execute, query, transaccion, uno_o_404
from utils import ErrorNegocio, datos_json, entero, opcion, param_entero, requeridos

bp = Blueprint("sanciones", __name__, url_prefix="/api/sanciones")

MOTIVOS = ("roja", "acumulacion de amarillas", "disciplinaria")


def _datos_fechas(datos):
    requeridos(datos, ["numero_fecha_inicio", "cantidad_fechas"])
    return (entero(datos["numero_fecha_inicio"], "numero_fecha_inicio", minimo=1),
            entero(datos["cantidad_fechas"], "cantidad_fechas", minimo=1))


@bp.get("")
@cualquier_rol
def listar():
    """Filtros opcionales: id_torneo, ci_jugador, numero_fecha (sanciones vigentes en esa fecha)."""
    condiciones, params = [], []
    for campo in ("id_torneo", "ci_jugador"):
        valor = param_entero(campo, requerido=False)
        if valor is not None:
            condiciones.append(f"s.{campo} = %s")
            params.append(valor)
    numero_fecha = param_entero("numero_fecha", requerido=False)
    if numero_fecha is not None:
        condiciones.append("%s BETWEEN s.numero_fecha_inicio AND s.numero_fecha_inicio + s.cantidad_fechas - 1")
        params.append(numero_fecha)
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    return jsonify(query(f"""
        SELECT s.id_sancion, s.id_torneo, s.ci_jugador, j.nombre, j.apellido,
               e.nombre AS equipo, s.motivo, s.numero_fecha_inicio, s.cantidad_fechas,
               s.numero_fecha_inicio + s.cantidad_fechas - 1 AS numero_fecha_fin,
               s.id_tarjeta_origen
        FROM sancion_jugador s
        JOIN jugador j ON j.ci = s.ci_jugador
        LEFT JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador
                                           AND ejt.id_torneo = s.id_torneo
        LEFT JOIN equipo e ON e.id_equipo = ejt.id_equipo
        {where}
        ORDER BY s.id_torneo, s.numero_fecha_inicio, j.apellido
    """, params))


@bp.post("")
@solo_admin
def crear():
    """Sanción cargada por la organización (por defecto, disciplinaria)."""
    datos = datos_json()
    requeridos(datos, ["ci_jugador", "id_torneo"])
    ci = entero(datos["ci_jugador"], "ci_jugador")
    id_torneo = entero(datos["id_torneo"], "id_torneo")
    motivo = opcion(datos.get("motivo", "disciplinaria"), MOTIVOS, "motivo")
    inicio, cantidad = _datos_fechas(datos)

    with transaccion() as cur:
        uno_o_404(cur, "SELECT 1 FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_torneo = %s",
                  (ci, id_torneo), "El jugador no está inscripto en esa edición del torneo")
        cur.execute("""
            INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            VALUES (%s, %s, %s, %s, %s)
        """, (ci, id_torneo, motivo, inicio, cantidad))
        id_sancion = cur.lastrowid
    return jsonify(mensaje="Sanción registrada", id_sancion=id_sancion), 201


@bp.put("/<int:id_sancion>")
@solo_admin
def modificar(id_sancion):
    inicio, cantidad = _datos_fechas(datos_json())
    if not query("SELECT 1 FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,), one=True):
        raise ErrorNegocio("Sanción no encontrada", 404)
    execute("""
        UPDATE sancion_jugador SET numero_fecha_inicio = %s, cantidad_fechas = %s
        WHERE id_sancion = %s
    """, (inicio, cantidad, id_sancion))
    return jsonify(mensaje="Sanción modificada")


@bp.delete("/<int:id_sancion>")
@solo_admin
def eliminar(id_sancion):
    if not query("SELECT 1 FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,), one=True):
        raise ErrorNegocio("Sanción no encontrada", 404)
    execute("DELETE FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
    return jsonify(mensaje="Sanción eliminada")
