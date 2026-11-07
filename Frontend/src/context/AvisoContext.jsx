import { createContext, useCallback, useContext, useMemo, useState } from "react";

const AvisoContext = createContext(null);

/** Mensajes flotantes de éxito o error. */
export function AvisoProvider({ children }) {
  const [avisos, setAvisos] = useState([]);

  const quitar = useCallback((id) => setAvisos((a) => a.filter((x) => x.id !== id)), []);

  const mostrar = useCallback(
    (tipo, texto) => {
      const id = `${Date.now()}-${Math.random()}`;
      setAvisos((a) => [...a, { id, tipo, texto }]);
      setTimeout(() => quitar(id), tipo === "error" ? 7000 : 3500);
    },
    [quitar]
  );

  const valor = useMemo(
    () => ({ ok: (t) => mostrar("ok", t), error: (t) => mostrar("error", t) }),
    [mostrar]
  );

  return (
    <AvisoContext.Provider value={valor}>
      {children}
      <div className="avisos" role="status">
        {avisos.map((a) => (
          <div key={a.id} className={`aviso aviso-${a.tipo}`} onClick={() => quitar(a.id)}>
            {a.texto}
          </div>
        ))}
      </div>
    </AvisoContext.Provider>
  );
}

export const useAviso = () => useContext(AvisoContext);
