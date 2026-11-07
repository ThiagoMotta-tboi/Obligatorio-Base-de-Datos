import { useState } from "react";
import { Link } from "react-router-dom";
import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import Formulario from "../components/Formulario.jsx";
import Modal from "../components/Modal.jsx";
import Tabla from "../components/Tabla.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useAviso } from "../context/AvisoContext.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { fmtFecha, opciones, useCarga } from "../util.js";

const ESTADOS = ["programado", "jugado", "postergado", "cancelado"];

export default function Partidos() {
  const { torneo } = useTorneo();
  const { esAdmin } = useAuth();
  const aviso = useAviso();
  const id = torneo?.id_torneo;
  const [fecha, setFecha] = useState("");
  const [estado, setEstado] = useState("");
  const [modal, setModal] = useState(null);

  const { datos: partidos, error, cargando, recargar } = useCarga(
    () => (id ? get(`/partidos?id_torneo=${id}`) : Promise.resolve([])),
    [id]
  );
  // Datos para el formulario de programación (solo administradores)
  const { datos: aux } = useCarga(
    () =>
      esAdmin && id
        ? Promise.all([get(`/equipos?id_torneo=${id}`), get("/turnos"), get("/canchas")]).then(
            ([equipos, turnos, canchas]) => ({ equipos, turnos, canchas })
          )
        : Promise.resolve(null),
    [esAdmin, id]
  );

  if (!torneo) return <p className="vacio">Seleccione una edición del torneo.</p>;

  const lista = partidos || [];
  const fechas = [...new Set(lista.map((p) => p.numero_fecha))].sort((a, b) => a - b);
  const filtrados = lista.filter(
    (p) => (!fecha || p.numero_fecha === Number(fecha)) && (!estado || p.estado === estado)
  );

  const accion = async (fn, mensaje) => {
    try {
      await fn();
      aviso.ok(mensaje);
      recargar();
    } catch (e) {
      aviso.error(e.message);
    }
  };

  const cambiarEstado = (p, nuevo) => {
    const textos = {
      jugado: "¿Marcar el partido como jugado? Desde ahí hay 48 horas para corregir la planilla.",
      postergado: "¿Postergar el partido?",
      cancelado: "¿Cancelar el partido? Los equipos podrán volver a programar su enfrentamiento.",
    };
    if (!window.confirm(textos[nuevo])) return;
    accion(() => put(`/partidos/${p.id_partido}/estado`, { estado: nuevo }), `Partido ${nuevo}`);
  };

  const eliminar = (p) => {
    if (!window.confirm(`¿Eliminar el partido ${p.equipo_local} vs ${p.equipo_visitante}?`)) return;
    accion(() => del(`/partidos/${p.id_partido}`), "Partido eliminado");
  };

  const guardar = async ({ cancha, ...valores }) => {
    const separador = cancha.indexOf("|");
    const cuerpo = {
      ...valores,
      id_complejo: Number(cancha.slice(0, separador)),
      nombre_cancha: cancha.slice(separador + 1),
    };
    if (modal.partido) {
      await put(`/partidos/${modal.partido.id_partido}`, cuerpo);
      aviso.ok("Partido reprogramado");
    } else {
      await post("/partidos", { ...cuerpo, id_torneo: id });
      aviso.ok("Partido programado");
    }
    setModal(null);
    recargar();
  };

  const proximaFecha = fechas.length ? Math.max(...fechas) : 1;

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Partidos</h1>
          <p className="apagado">{torneo.nombre}</p>
        </div>
        <div className="herramientas">
          <select value={fecha} onChange={(e) => setFecha(e.target.value)} aria-label="Filtrar por fecha">
            <option value="">Todas las fechas</option>
            {fechas.map((f) => (
              <option key={f} value={f}>
                Fecha {f}
              </option>
            ))}
          </select>
          <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Filtrar por estado">
            <option value="">Todos los estados</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
          {esAdmin && torneo.estado !== "finalizado" && (
            <button className="boton" onClick={() => setModal({ partido: null })} disabled={!aux}>
              + Programar partido
            </button>
          )}
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <Tabla
        filas={filtrados}
        clave={(p) => p.id_partido}
        cargando={cargando}
        vacio="No hay partidos para mostrar"
        columnas={[
          { campo: "numero_fecha", titulo: "Fecha", alinear: "centro" },
          {
            campo: "dia",
            titulo: "Día y turno",
            render: (p) => (
              <>
                {fmtFecha(p.dia)}
                <br />
                <span className="apagado">
                  {p.hora_inicio} – {p.hora_fin}
                </span>
              </>
            ),
          },
          {
            campo: "cancha",
            titulo: "Cancha",
            render: (p) => (
              <>
                {p.nombre_cancha}
                <br />
                <span className="apagado">{p.complejo}</span>
              </>
            ),
          },
          {
            campo: "partido",
            titulo: "Partido",
            render: (p) => (
              <div className="marcador">
                <span>{p.equipo_local}</span>
                <strong>{p.estado === "jugado" ? `${p.goles_local} – ${p.goles_visitante}` : "vs"}</strong>
                <span>{p.equipo_visitante}</span>
              </div>
            ),
          },
          { campo: "estado", titulo: "Estado", render: (p) => <Etiqueta valor={p.estado} /> },
        ]}
        acciones={(p) => (
          <>
            <Link className="boton chico" to={`/partidos/${p.id_partido}`}>
              {p.estado === "programado" ? "Planilla" : "Ver"}
            </Link>
            {p.estado === "programado" && new Date(`${p.dia}T${p.hora_fin}:00`) <= new Date() && (
              <button className="boton secundario chico" onClick={() => cambiarEstado(p, "jugado")}>
                Marcar jugado
              </button>
            )}
            {esAdmin && ["programado", "postergado"].includes(p.estado) && (
              <>
                <button className="boton secundario chico" onClick={() => setModal({ partido: p })} disabled={!aux}>
                  Reprogramar
                </button>
                {p.estado === "programado" && (
                  <button className="boton secundario chico" onClick={() => cambiarEstado(p, "postergado")}>
                    Postergar
                  </button>
                )}
                <button className="boton secundario chico" onClick={() => cambiarEstado(p, "cancelado")}>
                  Cancelar
                </button>
              </>
            )}
            {esAdmin && p.estado !== "jugado" && (
              <button className="boton peligro chico" onClick={() => eliminar(p)}>
                Eliminar
              </button>
            )}
          </>
        )}
      />

      {modal && aux && (
        <Modal titulo={modal.partido ? "Reprogramar partido" : "Programar partido"} onClose={() => setModal(null)}>
          <Formulario
            campos={camposPartido(aux)}
            inicial={
              modal.partido
                ? { ...modal.partido, cancha: `${modal.partido.id_complejo}|${modal.partido.nombre_cancha}` }
                : { numero_fecha: proximaFecha }
            }
            onSubmit={guardar}
            onCancel={() => setModal(null)}
            textoBoton={modal.partido ? "Reprogramar" : "Programar"}
          />
        </Modal>
      )}
    </>
  );
}

function camposPartido({ equipos, turnos, canchas }) {
  const opcionesEquipos = opciones(equipos, "id_equipo", (e) => `${e.nombre} (${e.jugadores} jug.)`);
  return [
    { nombre: "numero_fecha", etiqueta: "Fecha del torneo", tipo: "number", requerido: true, min: 1 },
    { nombre: "dia", etiqueta: "Día", tipo: "date", requerido: true },
    { nombre: "id_equipo_local", etiqueta: "Equipo local", tipo: "select", numero: true, requerido: true, opciones: opcionesEquipos },
    { nombre: "id_equipo_visitante", etiqueta: "Equipo visitante", tipo: "select", numero: true, requerido: true, opciones: opcionesEquipos },
    {
      nombre: "id_turno",
      etiqueta: "Turno",
      tipo: "select",
      numero: true,
      requerido: true,
      opciones: opciones(turnos, "id_turno", (t) => `${t.hora_inicio} a ${t.hora_fin}`),
    },
    {
      nombre: "cancha",
      etiqueta: "Cancha",
      tipo: "select",
      requerido: true,
      opciones: canchas.map((c) => ({ valor: `${c.id_complejo}|${c.nombre_cancha}`, etiqueta: `${c.complejo} · ${c.nombre_cancha}` })),
    },
  ];
}
