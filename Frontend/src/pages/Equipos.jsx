import { Link } from "react-router-dom";
import { del, get, post, put } from "../api.js";
import PaginaABM from "../components/PaginaABM.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { opciones, useCarga } from "../util.js";

export default function Equipos() {
  const { torneo, recargarTorneos } = useTorneo();
  const { datos: facultades } = useCarga(() => get("/facultades"), []);
  const id = torneo?.id_torneo;

  if (!torneo) return <p className="vacio">Seleccione una edición del torneo.</p>;
  const enInscripcion = torneo.estado === "inscripcion";

  return (
    <PaginaABM
      titulo="Equipos y planteles"
      subtitulo={torneo.nombre}
      textoNuevo="Nuevo equipo"
      cargar={() => get(`/equipos?id_torneo=${id}`)}
      deps={[id]}
      clave={(e) => e.id_equipo}
      aviso={
        !enInscripcion && (
          <p className="nota">
            El torneo está <strong>{torneo.estado}</strong>: no se pueden inscribir equipos ni modificar planteles.
          </p>
        )
      }
      columnas={[
        { campo: "nombre", titulo: "Equipo", render: (e) => <Link to={`/equipos/${e.id_equipo}`}>{e.nombre}</Link> },
        { campo: "facultad", titulo: "Facultad" },
        { campo: "capitan", titulo: "Capitán", render: (e) => e.capitan || <span className="apagado">Sin asignar</span> },
        {
          campo: "jugadores",
          titulo: "Plantel",
          alinear: "centro",
          render: (e) => (
            <span className={e.jugadores < 5 ? "texto-alerta" : ""}>{e.jugadores} / 10</span>
          ),
        },
      ]}
      campos={[
        { nombre: "nombre", etiqueta: "Nombre", requerido: true },
        {
          nombre: "id_facultad",
          etiqueta: "Facultad",
          tipo: "select",
          numero: true,
          requerido: true,
          opciones: opciones(facultades, "id_facultad", "nombre"),
        },
      ]}
      crear={enInscripcion ? (v) => post("/equipos", { ...v, id_torneo: id }) : undefined}
      modificar={(e, v) => put(`/equipos/${e.id_equipo}`, v)}
      eliminar={enInscripcion ? (e) => del(`/equipos/${e.id_equipo}`) : undefined}
      describir={(e) => `el equipo ${e.nombre} y su plantel`}
      alCambiar={() => recargarTorneos().catch(() => {})}
      acciones={(e) => (
        <Link className="boton chico" to={`/equipos/${e.id_equipo}`}>
          Plantel
        </Link>
      )}
    />
  );
}
