import { useCallback, useEffect, useState } from "react";

export const TIPOS_JUGADOR = ["grado", "posgrado", "docente", "funcionario"];
export const SUPERFICIES = ["sintetico", "parquet"];
export const MOTIVOS_SANCION = ["roja", "acumulacion de amarillas", "disciplinaria"];

export const SIGUIENTE_ETAPA = { inscripcion: "en curso", "en curso": "finalizado" };

// "2026-10-05" -> "05/10/2026"
export function fmtFecha(iso) {
  if (!iso) return "";
  const [anio, mes, dia] = String(iso).slice(0, 10).split("-");
  return `${dia}/${mes}/${anio}`;
}

export function nombreCompleto(j) {
  return `${j.nombre} ${j.apellido}`;
}

// Convierte una lista de objetos en opciones para un <select>
export function opciones(lista, campoValor, etiqueta) {
  return (lista || []).map((x) => ({
    valor: x[campoValor],
    etiqueta: typeof etiqueta === "function" ? etiqueta(x) : x[etiqueta],
  }));
}

export function opcionesTexto(lista) {
  return lista.map((x) => ({ valor: x, etiqueta: x }));
}

/** Ejecuta una carga asíncrona y expone datos, error, estado y una función para recargar. */
export function useCarga(cargar, deps) {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const recargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      setDatos(await cargar());
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, deps);

  useEffect(() => {
    recargar();
  }, [recargar]);

  return { datos, error, cargando, recargar };
}
