"""Crea o actualiza un usuario del sistema guardando la contraseña con hash bcrypt.

Uso:
    python crear_usuario.py <correo> <contraseña> <administrador|planillero>
"""
import sys

import bcrypt

from db import execute

if len(sys.argv) != 4 or sys.argv[3] not in ("administrador", "planillero"):
    print(__doc__)
    sys.exit(1)

correo, password, rol = sys.argv[1:]
hash_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

execute("""
    INSERT INTO login (correo, password, rol) VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE password = VALUES(password), rol = VALUES(rol)
""", (correo, hash_password, rol))

print(f"Usuario {correo} ({rol}) guardado")
