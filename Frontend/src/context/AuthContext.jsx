import { createContext, useCallback, useContext, useState } from "react";
import { almacen, post, setOnUnauthorized, setToken } from "../api.js";

const AuthContext = createContext(null);

function sesionGuardada() {
  try {
    return JSON.parse(almacen.leer("sesion")) || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  // El token se configura de inmediato para que las primeras cargas ya lo usen
  const [sesion, setSesion] = useState(() => {
    const guardada = sesionGuardada();
    setToken(guardada?.token ?? null);
    return guardada;
  });

  const logout = useCallback(() => {
    almacen.guardar("sesion", null);
    setToken(null);
    setSesion(null);
  }, []);

  const login = useCallback(async (correo, password) => {
    const datos = await post("/auth/login", { correo, password });
    const nueva = { token: datos.token, correo: datos.correo, rol: datos.rol };
    almacen.guardar("sesion", JSON.stringify(nueva));
    setToken(nueva.token);
    setSesion(nueva);
  }, []);

  setOnUnauthorized(logout);

  const valor = {
    sesion,
    login,
    logout,
    esAdmin: sesion?.rol === "administrador",
  };
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
