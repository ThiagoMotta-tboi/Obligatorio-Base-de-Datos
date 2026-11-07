/**
 * Tabla genérica.
 * columnas: [{ campo, titulo, render?(fila), alinear?: "centro" | "derecha" }]
 */
export default function Tabla({ columnas, filas, clave, acciones, cargando, vacio = "No hay datos para mostrar" }) {
  if (cargando && !filas?.length) return <p className="apagado">Cargando…</p>;
  if (!filas?.length) return <p className="vacio">{vacio}</p>;

  return (
    <div className="tabla-contenedor">
      <table className="tabla">
        <thead>
          <tr>
            {columnas.map((c) => (
              <th key={c.campo} className={c.alinear || ""}>
                {c.titulo}
              </th>
            ))}
            {acciones && <th className="derecha">Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila, i) => (
            <tr key={clave ? clave(fila) : i}>
              {columnas.map((c) => (
                <td key={c.campo} className={c.alinear || ""}>
                  {c.render ? c.render(fila, i) : fila[c.campo]}
                </td>
              ))}
              {acciones && <td className="acciones">{acciones(fila)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
