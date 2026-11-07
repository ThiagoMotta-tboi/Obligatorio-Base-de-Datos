import { useState } from "react";
import { almacen, get } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import Tabla from "../components/Tabla.jsx";
import TablaPosiciones from "../components/TablaPosiciones.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { TIPOS_JUGADOR, nombreCompleto, useCarga } from "../util.js";

const puesto = { campo: "puesto", titulo: "#", alinear: "centro", render: (_, i) => i + 1 };
const jugador = { campo: "jugador", titulo: "Jugador", render: nombreCompleto };

// Columna numérica que se dibuja con una barra proporcional al máximo
const conBarra = (campo, titulo) => ({ campo, titulo, barra: true });

const REPORTES = [
  { id: "posiciones", titulo: "Tabla de posiciones", especial: "posiciones" },
  {
    id: "goleadores",
    titulo: "Goleadores",
    descripcion: "Los 10 jugadores con más goles (sin contar autogoles).",
    columnas: [puesto, jugador, { campo: "equipo", titulo: "Equipo" }, conBarra("goles", "Goles")],
  },
  {
    id: "fair-play",
    titulo: "Fair play",
    descripcion: "1 punto por amarilla y 3 por roja. El mejor equipo es el de menor puntaje.",
    columnas: [
      puesto,
      { campo: "equipo", titulo: "Equipo" },
      { campo: "amarillas", titulo: "Amarillas", alinear: "centro" },
      { campo: "rojas", titulo: "Rojas", alinear: "centro" },
      { campo: "puntaje", titulo: "Puntaje", alinear: "centro", render: (f) => <strong>{f.puntaje}</strong> },
    ],
  },
  { id: "promedio-goles", titulo: "Promedio de goles", especial: "promedio" },
  {
    id: "canchas",
    titulo: "Canchas más utilizadas",
    descripcion: "Partidos jugados o programados en cada cancha.",
    columnas: [{ campo: "complejo", titulo: "Complejo" }, { campo: "nombre_cancha", titulo: "Cancha" }, conBarra("partidos", "Partidos")],
  },
  {
    id: "turnos",
    titulo: "Turnos más utilizados",
    descripcion: "Partidos jugados o programados en cada turno.",
    columnas: [{ campo: "turno", titulo: "Turno", render: (f) => `${f.hora_inicio} a ${f.hora_fin}` }, conBarra("partidos", "Partidos")],
  },
  { id: "jugadores-por-facultad", titulo: "Jugadores por facultad y tipo", especial: "facultades" },
  {
    id: "jugadores-sin-jugar",
    titulo: "Inscriptos que nunca jugaron",
    descripcion: "Jugadores del plantel que no figuran en ninguna planilla de la edición.",
    columnas: [{ campo: "ci", titulo: "Cédula" }, jugador, { campo: "equipo", titulo: "Equipo" }],
  },
  {
    id: "sanciones",
    titulo: "Sanciones por equipo y motivo",
    columnas: [
      { campo: "equipo", titulo: "Equipo" },
      { campo: "motivo", titulo: "Motivo", render: (f) => <Etiqueta valor={f.motivo} /> },
      { campo: "cantidad", titulo: "Cantidad", alinear: "centro" },
    ],
  },
  {
    id: "estado-partidos",
    titulo: "Partidos jugados vs. postergados y cancelados",
    columnas: [
      { campo: "estado", titulo: "Estado", render: (f) => <Etiqueta valor={f.estado} /> },
      { campo: "cantidad", titulo: "Partidos", alinear: "centro" },
      conBarra("porcentaje", "Porcentaje"),
    ],
    sufijo: { porcentaje: "%" },
  },
  {
    id: "suspendidos",
    titulo: "Suspendidos por fecha",
    propio: true,
    descripcion: "Jugadores que no pueden figurar en la planilla de una fecha.",
    conFecha: true,
    columnas: [
      jugador,
      { campo: "equipo", titulo: "Equipo" },
      { campo: "motivo", titulo: "Motivo", render: (f) => <Etiqueta valor={f.motivo} /> },
      { campo: "rango", titulo: "Fechas", render: (f) => (f.desde === f.hasta ? `${f.desde}` : `${f.desde} a ${f.hasta}`) },
    ],
  },
  {
    id: "goles-por-tramo",
    titulo: "Goles por tramo de minutos",
    propio: true,
    descripcion: "En qué momento del partido se convierten más goles.",
    columnas: [{ campo: "tramo", titulo: "Minutos" }, conBarra("goles", "Goles")],
  },
  {
    id: "edad-promedio",
    titulo: "Edad promedio por equipo",
    propio: true,
    columnas: [
      { campo: "equipo", titulo: "Equipo" },
      { campo: "edad_promedio", titulo: "Promedio", alinear: "centro" },
      { campo: "mas_joven", titulo: "Más joven", alinear: "centro" },
      { campo: "mas_grande", titulo: "Más grande", alinear: "centro" },
    ],
  },
];

export default function Reportes() {
  const { torneo } = useTorneo();
  const [idReporte, setIdReporte] = useState(() => almacen.leer("reporte") || "posiciones");
  const [numeroFecha, setNumeroFecha] = useState(1);
  const [soloInscriptos, setSoloInscriptos] = useState(false);

  const reporte = REPORTES.find((r) => r.id === idReporte) || REPORTES[0];
  const id = torneo?.id_torneo;

  const { datos, error, cargando } = useCarga(() => {
    if (!id) return Promise.resolve(null);
    const params = new URLSearchParams();
    if (reporte.id !== "jugadores-por-facultad" || soloInscriptos) params.set("id_torneo", id);
    if (reporte.conFecha) params.set("numero_fecha", numeroFecha);
    return get(`/reportes/${reporte.id}?${params}`);
  }, [reporte.id, id, numeroFecha, soloInscriptos]);

  const elegir = (r) => {
    setIdReporte(r);
    almacen.guardar("reporte", r);
  };

  if (!torneo) return <p className="vacio">Seleccione una edición del torneo.</p>;

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Reportes</h1>
          <p className="apagado">{torneo.nombre}</p>
        </div>
      </div>

      <div className="reportes">
        <nav className="menu-reportes" aria-label="Reportes">
          {REPORTES.map((r) => (
            <button key={r.id} className={r.id === reporte.id ? "activo" : ""} onClick={() => elegir(r.id)}>
              {r.titulo}
              {r.propio && <small>propuesto</small>}
            </button>
          ))}
        </nav>

        <section className="tarjeta">
          <div className="encabezado">
            <div>
              <h2>{reporte.titulo}</h2>
              {reporte.descripcion && <p className="apagado">{reporte.descripcion}</p>}
            </div>
            {reporte.conFecha && (
              <label className="campo-chico">
                Fecha
                <input type="number" min="1" value={numeroFecha} onChange={(e) => setNumeroFecha(Number(e.target.value) || 1)} />
              </label>
            )}
            {reporte.especial === "facultades" && (
              <label className="campo-check">
                <input type="checkbox" checked={soloInscriptos} onChange={(e) => setSoloInscriptos(e.target.checked)} />
                Solo inscriptos en esta edición
              </label>
            )}
          </div>

          {error && <p className="error">{error}</p>}
          {!error && <Contenido reporte={reporte} datos={datos} cargando={cargando} />}
        </section>
      </div>
    </>
  );
}

function Contenido({ reporte, datos, cargando }) {
  if (cargando && !datos) return <p className="apagado">Cargando…</p>;
  if (!datos) return null;

  if (reporte.especial === "posiciones") return <TablaPosiciones filas={datos} />;
  if (reporte.especial === "promedio") return <PromedioGoles datos={datos} />;
  if (reporte.especial === "facultades") return <PorFacultad filas={datos} />;

  // Las columnas con barra se dibujan proporcionales al valor máximo
  const columnas = reporte.columnas.map((c) => {
    if (!c.barra) return c;
    const maximo = Math.max(1, ...datos.map((f) => Number(f[c.campo]) || 0));
    const sufijo = reporte.sufijo?.[c.campo] || "";
    return {
      ...c,
      render: (f) => (
        <div className="barra-valor">
          <div className="barra-fondo">
            <div className="barra-relleno" style={{ width: `${((Number(f[c.campo]) || 0) / maximo) * 100}%` }} />
          </div>
          <span>
            {f[c.campo]}
            {sufijo}
          </span>
        </div>
      ),
    };
  });

  return <Tabla columnas={columnas} filas={datos} />;
}

function PromedioGoles({ datos }) {
  return (
    <>
      <div className="indicadores">
        <div className="indicador">
          <strong>{datos.edicion.promedio ?? "—"}</strong>
          <span>Goles por partido en la edición</span>
        </div>
        <div className="indicador">
          <strong>{datos.edicion.goles}</strong>
          <span>Goles en {datos.edicion.partidos} partidos</span>
        </div>
      </div>
      <Tabla
        filas={datos.por_fecha}
        vacio="Todavía no hay partidos jugados"
        columnas={[
          { campo: "numero_fecha", titulo: "Fecha", alinear: "centro" },
          { campo: "partidos", titulo: "Partidos", alinear: "centro" },
          { campo: "goles", titulo: "Goles", alinear: "centro" },
          { campo: "promedio", titulo: "Promedio", alinear: "centro", render: (f) => <strong>{f.promedio}</strong> },
        ]}
      />
    </>
  );
}

// Tabla cruzada: una fila por facultad y una columna por tipo de jugador
function PorFacultad({ filas }) {
  const facultades = {};
  for (const f of filas) {
    facultades[f.facultad] ??= { facultad: f.facultad, total: 0 };
    facultades[f.facultad][f.tipo] = f.cantidad;
    facultades[f.facultad].total += f.cantidad;
  }
  return (
    <Tabla
      filas={Object.values(facultades)}
      vacio="No hay jugadores"
      columnas={[
        { campo: "facultad", titulo: "Facultad" },
        ...TIPOS_JUGADOR.map((t) => ({ campo: t, titulo: t[0].toUpperCase() + t.slice(1), alinear: "centro", render: (f) => f[t] || 0 })),
        { campo: "total", titulo: "Total", alinear: "centro", render: (f) => <strong>{f.total}</strong> },
      ]}
    />
  );
}
