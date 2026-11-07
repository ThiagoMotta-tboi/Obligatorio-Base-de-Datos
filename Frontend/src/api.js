// Cliente de la API del backend. Agrega el token y convierte los errores en mensajes legibles.

const BASE = "/api";

let token = null;
let alExpirarSesion = null;

export function setToken(nuevo) {
  token = nuevo;
}

export function setOnUnauthorized(fn) {
  alExpirarSesion = fn;
}

export class ApiError extends Error {
  constructor(mensaje, status) {
    super(mensaje);
    this.status = status;
  }
}

async function api(ruta, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  let respuesta;
  try {
    respuesta = await fetch(BASE + ruta, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor. ¿Está corriendo el backend?", 0);
  }

  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    // Token vencido o inválido: se cierra la sesión (salvo en el propio login)
    if (respuesta.status === 401 && ruta !== "/auth/login" && alExpirarSesion) {
      alExpirarSesion();
    }
    const mensaje = datos?.error || datos?.msg || `Error ${respuesta.status}`;
    throw new ApiError(datos?.detalle ? `${mensaje} (${datos.detalle})` : mensaje, respuesta.status);
  }
  return datos;
}

export const get = (ruta) => api(ruta);
export const post = (ruta, body) => api(ruta, { method: "POST", body });
export const put = (ruta, body) => api(ruta, { method: "PUT", body });
export const del = (ruta) => api(ruta, { method: "DELETE" });

// localStorage puede no estar disponible (modo privado, permisos)
export const almacen = {
  leer(clave) {
    try {
      return localStorage.getItem(clave);
    } catch {
      return null;
    }
  },
  guardar(clave, valor) {
    try {
      if (valor == null) localStorage.removeItem(clave);
      else localStorage.setItem(clave, valor);
    } catch {
      /* sin almacenamiento: se pierde al recargar */
    }
  },
};
