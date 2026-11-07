import { Link } from "react-router-dom";
import { get } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import TablaPosiciones from "../components/TablaPosiciones.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";
import { fmtFecha, useCarga } from "../util.js";

export default function Inicio() {
  const { torneo } = useTorneo();
  const id = torneo?.id_torneo;

  const { datos, cargando, error } = useCarga(
    () =>
      id
        ? Promise.all([
            get(`/reportes/posiciones?id_torneo=${id}`),
            get(`/partidos?id_torneo=${id}`),
            get(`/partidos?id_torneo=${id}&pendientes=1`),
          ])
        : Promise.resolve(null),
    [id]
  );

  if (!torneo) return <p className="vacio">No hay torneos cargados.</p>;

  const [posiciones, partidos, pendientes] = datos || [[], [], []];
  const jugados = partidos.filter((p) => p.estado === "jugado").length;
  const hoy = new Date().toISOString().slice(0, 10);
  const proximos = partidos.filter((p) => p.estado === "programado" && p.dia >= hoy).slice(0, 5);

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>{torneo.nombre}</h1>
          <p className="apagado">
            Del {fmtFecha(torneo.fecha_inicio)} al {fmtFecha(torneo.fecha_fin)}
          </p>
        </div>
        <Etiqueta valor={torneo.estado} />
      </div>
      {error && <p className="error">{error}</p>}

      <div className="indicadores">
        <Indicador valor={torneo.equipos} texto="Equipos" />
        <Indicador valor={`${jugados} / ${partidos.length}`} texto="Partidos jugados" />
        <Indicador valor={pendientes.length} texto="Planillas pendientes" alerta={pendientes.length > 0} />
      </div>

      <div className="columnas">
        <section className="tarjeta">
          <h2>Tabla de posiciones</h2>
          <TablaPosiciones filas={posiciones} cargando={cargando} />
        </section>

        <div className="pila">
          {pendientes.length > 0 && (
            <section className="tarjeta">
              <h2>Planillas pendientes</h2>
              <p className="apagado">Partidos ya disputados que todavía no se marcaron como jugados.</p>
              <ListaPartidos partidos={pendientes} />
            </section>
          )}
          <section className="tarjeta">
            <h2>Próximos partidos</h2>
            {proximos.length ? <ListaPartidos partidos={proximos} /> : <p className="vacio">No hay partidos programados.</p>}
          </section>
        </div>
      </div>
    </>
  );
}

function Indicador({ valor, texto, alerta }) {
  return (
    <div className={`indicador ${alerta ? "alerta" : ""}`}>
      <strong>{valor}</strong>
      <span>{texto}</span>
    </div>
  );
}

function ListaPartidos({ partidos }) {
  return (
    <ul className="lista-partidos">
      {partidos.map((p) => (
        <li key={p.id_partido}>
          <Link to={`/partidos/${p.id_partido}`}>
            <span className="apagado">
              Fecha {p.numero_fecha} · {fmtFecha(p.dia)} {p.hora_inicio}
            </span>
            <span>
              {p.equipo_local} <span className="apagado">vs</span> {p.equipo_visitante}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
