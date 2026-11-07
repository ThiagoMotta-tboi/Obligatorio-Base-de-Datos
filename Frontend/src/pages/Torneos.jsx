import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import PaginaABM from "../components/PaginaABM.jsx";
import { useAviso } from "../context/AvisoContext.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { SIGUIENTE_ETAPA, fmtFecha } from "../util.js";

const CAMPOS = [
  { nombre: "nombre", etiqueta: "Nombre", requerido: true },
  { nombre: "anio", etiqueta: "Año", tipo: "number", requerido: true, min: 2000 },
  {
    nombre: "semestre",
    etiqueta: "Semestre",
    tipo: "select",
    numero: true,
    requerido: true,
    opciones: [
      { valor: 1, etiqueta: "Primer semestre" },
      { valor: 2, etiqueta: "Segundo semestre" },
    ],
  },
  { nombre: "fecha_inicio", etiqueta: "Fecha de inicio", tipo: "date", requerido: true },
  { nombre: "fecha_fin", etiqueta: "Fecha de fin", tipo: "date", requerido: true },
];

export default function Torneos() {
  const aviso = useAviso();
  const { recargarTorneos } = useTorneo();

  const avanzar = async (t, listo) => {
    const siguiente = SIGUIENTE_ETAPA[t.estado];
    if (!window.confirm(`¿Pasar "${t.nombre}" a la etapa "${siguiente}"? No se puede volver atrás.`)) return;
    try {
      await put(`/torneos/${t.id_torneo}/estado`, { estado: siguiente });
      aviso.ok(`El torneo pasó a "${siguiente}"`);
      listo();
    } catch (e) {
      aviso.error(e.message);
    }
  };

  return (
    <PaginaABM
      titulo="Torneos"
      subtitulo="Cada edición pasa por las etapas inscripción → en curso → finalizado"
      textoNuevo="Nuevo torneo"
      cargar={() => get("/torneos")}
      clave={(t) => t.id_torneo}
      columnas={[
        { campo: "nombre", titulo: "Nombre" },
        { campo: "periodo", titulo: "Período", render: (t) => `${t.anio} · S${t.semestre}` },
        { campo: "fechas", titulo: "Fechas", render: (t) => `${fmtFecha(t.fecha_inicio)} – ${fmtFecha(t.fecha_fin)}` },
        { campo: "equipos", titulo: "Equipos", alinear: "centro" },
        { campo: "estado", titulo: "Etapa", render: (t) => <Etiqueta valor={t.estado} /> },
      ]}
      campos={CAMPOS}
      crear={(v) => post("/torneos", v)}
      modificar={(t, v) => put(`/torneos/${t.id_torneo}`, v)}
      eliminar={(t) => del(`/torneos/${t.id_torneo}`)}
      describir={(t) => `el torneo ${t.nombre}`}
      alCambiar={() => recargarTorneos().catch(() => {})}
      acciones={(t, listo) =>
        SIGUIENTE_ETAPA[t.estado] && (
          <button className="boton chico" onClick={() => avanzar(t, listo)}>
            Pasar a {SIGUIENTE_ETAPA[t.estado]}
          </button>
        )
      }
    />
  );
}
