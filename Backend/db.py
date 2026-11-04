from contextlib import contextmanager

import mysql.connector

from config import DB_CONFIG
from utils import ErrorNegocio


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def transaccion():
    """Abre una conexión y un cursor; hace commit al salir o rollback si hubo error.

    Se usa cuando una operación necesita varias consultas que deben
    validarse y aplicarse juntas (todo o nada).
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def todos(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


def uno(cur, sql, params=()):
    filas = todos(cur, sql, params)
    return filas[0] if filas else None


def uno_o_404(cur, sql, params, mensaje):
    fila = uno(cur, sql, params)
    if fila is None:
        raise ErrorNegocio(mensaje, 404)
    return fila


def query(sql, params=(), one=False):
    """SELECT simple: lista de diccionarios, o uno solo si one=True."""
    with transaccion() as cur:
        filas = todos(cur, sql, params)
    if one:
        return filas[0] if filas else None
    return filas


def execute(sql, params=()):
    """INSERT / UPDATE / DELETE simple: hace commit y devuelve el id generado."""
    with transaccion() as cur:
        cur.execute(sql, params)
        return cur.lastrowid
