import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import PaginaABM from "../components/PaginaABM.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { MOTIVOS_SANCION, nombreCompleto, opcionesTexto, useCarga } from "../util.js";

const CAMPOS_FECHAS = [
  { nombre: "numero_fecha_inicio", etiqueta: "Desde la fecha", tipo: "number", requerido: true, min: 1 },
  { nombre: "cantidad_fechas", etiqueta: "Cantidad de fechas", tipo: "number", requerido: true, min: 1, defecto: 1 },
];

export default function Sanciones() {
  const { torneo } = useTorneo();
  const id = torneo?.id_torneo;

  // Solo se pueden sancionar jugadores inscriptos en la edición
  const { datos: inscriptos } = useCarga(
    () =>
      id
        ? get(`/equipos?id_torneo=${id}`).then((equipos) =>
            Promise.all(equipos.map((e) => get(`/equipos/${e.id_equipo}/jugadores`).then((p) => p.map((j) => ({ ...j, equipo: e.nombre })))))
          )
        : Promise.resolve([]),
    [id]
  );

  if (!torneo) return <p className="vacio">Seleccione una edición del torneo.</p>;

  const jugadores = (inscriptos || []).flat().sort((a, b) => a.apellido.localeCompare(b.apellido));

  return (
    <PaginaABM
      titulo="Sanciones"
      subtitulo="Las sanciones por roja y por acumulación de amarillas se generan solas al cargar las tarjetas"
      textoNuevo="Nueva sanción"
      cargar={() => get(`/sanciones?id_torneo=${id}`)}
      deps={[id]}
      clave={(s) => s.id_sancion}
      buscar={(s) => `${nombreCompleto(s)} ${s.equipo} ${s.motivo}`}
      vacio="No hay sanciones en esta edición"
      columnas={[
        { campo: "jugador", titulo: "Jugador", render: nombreCompleto },
        { campo: "equipo", titulo: "Equipo" },
        { campo: "motivo", titulo: "Motivo", render: (s) => <Etiqueta valor={s.motivo} /> },
        {
          campo: "fechas",
          titulo: "Suspendido",
          render: (s) =>
            s.cantidad_fechas === 1 ? `Fecha ${s.numero_fecha_inicio}` : `Fechas ${s.numero_fecha_inicio} a ${s.numero_fecha_fin}`,
        },
        { campo: "origen", titulo: "Origen", render: (s) => (s.id_tarjeta_origen ? "Automática" : "Manual") },
      ]}
      campos={(modo) =>
        modo === "alta"
          ? [
              {
                nombre: "ci_jugador",
                etiqueta: "Jugador",
                tipo: "select",
                numero: true,
                requerido: true,
                opciones: jugadores.map((j) => ({ valor: j.ci, etiqueta: `${j.apellido}, ${j.nombre} (${j.equipo})` })),
              },
              { nombre: "motivo", etiqueta: "Motivo", tipo: "select", requerido: true, defecto: "disciplinaria", opciones: opcionesTexto(MOTIVOS_SANCION) },
              ...CAMPOS_FECHAS,
            ]
          : CAMPOS_FECHAS
      }
      crear={(v) => post("/sanciones", { ...v, id_torneo: id })}
      modificar={(s, v) => put(`/sanciones/${s.id_sancion}`, v)}
      eliminar={(s) => del(`/sanciones/${s.id_sancion}`)}
      describir={(s) => `la sanción de ${nombreCompleto(s)}`}
    />
  );
}
