import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { almacen, get } from "../api.js";
import { useAuth } from "./AuthContext.jsx";

const TorneoContext = createContext(null);

/** Edición del torneo seleccionada; la usan equipos, partidos, sanciones y reportes. */
export function TorneoProvider({ children }) {
  const { sesion } = useAuth();
  const [torneos, setTorneos] = useState([]);
  const [idTorneo, setIdTorneo] = useState(() => Number(almacen.leer("torneo")) || null);

  const recargarTorneos = useCallback(async () => {
    const lista = await get("/torneos");
    setTorneos(lista);
    setIdTorneo((actual) =>
      lista.some((t) => t.id_torneo === actual) ? actual : lista[0]?.id_torneo ?? null
    );
  }, []);

  useEffect(() => {
    if (sesion) recargarTorneos().catch(() => setTorneos([]));
  }, [sesion, recargarTorneos]);

  const seleccionar = (id) => {
    setIdTorneo(id);
    almacen.guardar("torneo", String(id));
  };

  const torneo = torneos.find((t) => t.id_torneo === idTorneo) || null;

  return (
    <TorneoContext.Provider value={{ torneos, torneo, seleccionar, recargarTorneos }}>
      {children}
    </TorneoContext.Provider>
  );
}

export const useTorneo = () => useContext(TorneoContext);
