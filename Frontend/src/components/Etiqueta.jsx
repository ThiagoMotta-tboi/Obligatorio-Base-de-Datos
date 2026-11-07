/** Etiqueta de color para estados, motivos y tipos (la clase sale del valor). */
export default function Etiqueta({ valor, children }) {
  const clase = String(valor).toLowerCase().replace(/\s+/g, "-");
  return <span className={`etiqueta et-${clase}`}>{children ?? valor}</span>;
}
