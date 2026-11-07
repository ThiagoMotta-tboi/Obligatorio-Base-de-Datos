import Tabla from "./Tabla.jsx";

const COLUMNAS = [
  { campo: "posicion", titulo: "#", alinear: "centro", render: (_, i) => i + 1 },
  { campo: "equipo", titulo: "Equipo" },
  { campo: "pj", titulo: "PJ", alinear: "centro" },
  { campo: "pg", titulo: "PG", alinear: "centro" },
  { campo: "pe", titulo: "PE", alinear: "centro" },
  { campo: "pp", titulo: "PP", alinear: "centro" },
  { campo: "gf", titulo: "GF", alinear: "centro" },
  { campo: "gc", titulo: "GC", alinear: "centro" },
  { campo: "dg", titulo: "DG", alinear: "centro", render: (f) => (f.dg > 0 ? `+${f.dg}` : f.dg) },
  { campo: "pts", titulo: "Pts", alinear: "centro", render: (f) => <strong>{f.pts}</strong> },
];

export default function TablaPosiciones({ filas, cargando }) {
  return (
    <Tabla
      columnas={COLUMNAS}
      filas={filas}
      clave={(f) => f.id_equipo}
      cargando={cargando}
      vacio="El torneo no tiene equipos inscriptos"
    />
  );
}
