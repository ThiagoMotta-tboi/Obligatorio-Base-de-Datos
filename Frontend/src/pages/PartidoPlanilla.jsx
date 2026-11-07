import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import Formulario from "../components/Formulario.jsx";
import Tabla from "../components/Tabla.jsx";
import { useAviso } from "../context/AvisoContext.jsx";
import { fmtFecha, nombreCompleto, useCarga } from "../util.js";

/** Pantalla del planillero: planilla de juego, goles y tarjetas de un partido. */
export default function PartidoPlanilla() {
  const { id } = useParams();
  const aviso = useAviso();
  const [claveGol, setClaveGol] = useState(0);
  const [claveTarjeta, setClaveTarjeta] = useState(0);

  const { datos, error, recargar } = useCarga(
    () => Promise.all([get(`/partidos/${id}`), get(`/partidos/${id}/jugadores`)]),
    [id]
  );

  if (error) return <p className="error">{error}</p>;
  if (!datos) return <p className="apagado">Cargando…</p>;

  const [partido, jugadores] = datos;
  // Mismas reglas que valida el backend, para no ofrecer acciones que va a rechazar
  const ahora = new Date();
  const noDisputado = ahora < new Date(`${partido.dia}T${partido.hora_fin}:00`);
  const plazoVencido =
    partido.estado === "jugado" && ahora - new Date(partido.fecha_jugado) > 48 * 60 * 60 * 1000;
  const bloqueado = ["postergado", "cancelado"].includes(partido.estado) || noDisputado || plazoVencido;
  const nombreEquipo = (idEquipo) =>
    idEquipo === partido.id_equipo_local ? partido.equipo_local : partido.equipo_visitante;

  const accion = async (fn, mensaje) => {
    try {
      const resultado = await fn();
      aviso.ok(typeof mensaje === "function" ? mensaje(resultado) : mensaje);
      await recargar();
    } catch (e) {
      aviso.error(e.message);
    }
  };

  const marcarJugado = () => {
    if (!window.confirm("¿Marcar el partido como jugado? Desde ahí hay 48 horas para corregir la planilla.")) return;
    accion(() => put(`/partidos/${id}/estado`, { estado: "jugado" }), "Partido marcado como jugado");
  };

  const registrarGol = async (v) => {
    await post(`/partidos/${id}/goles`, v);
    aviso.ok("Gol registrado");
    setClaveGol((k) => k + 1);
    await recargar();
  };

  const registrarTarjeta = async (v) => {
    const r = await post(`/partidos/${id}/tarjetas`, v);
    aviso.ok(
      r.sancion_generada
        ? `Tarjeta registrada. Sanción automática: suspendido en la fecha ${r.sancion_generada.numero_fecha_inicio}`
        : "Tarjeta registrada"
    );
    setClaveTarjeta((k) => k + 1);
    await recargar();
  };

  const opcionesPlanilla = partido.planilla.map((j) => ({
    valor: j.ci,
    etiqueta: `${nombreCompleto(j)} (${j.equipo})`,
  }));

  return (
    <>
      <Link to="/partidos" className="volver">
        ← Partidos
      </Link>

      <section className="tarjeta cabecera-partido">
        <p className="apagado">
          Fecha {partido.numero_fecha} · {fmtFecha(partido.dia)} · {partido.hora_inicio} a {partido.hora_fin} ·{" "}
          {partido.nombre_cancha}, {partido.complejo}
        </p>
        <div className="marcador grande">
          <span>{partido.equipo_local}</span>
          <strong>
            {partido.estado === "jugado" ? `${partido.goles_local} – ${partido.goles_visitante}` : golesParciales(partido)}
          </strong>
          <span>{partido.equipo_visitante}</span>
        </div>
        <div className="fila-centro">
          <Etiqueta valor={partido.estado} />
          {partido.estado === "programado" && !noDisputado && (
            <button className="boton" onClick={marcarJugado}>
              Marcar como jugado
            </button>
          )}
        </div>
        <p className="nota">{explicacion(partido, noDisputado, plazoVencido)}</p>
      </section>

      <div className="columnas iguales">
        {[partido.id_equipo_local, partido.id_equipo_visitante].map((idEquipo) => (
          <PlantelEquipo
            key={idEquipo}
            nombre={nombreEquipo(idEquipo)}
            jugadores={jugadores.filter((j) => j.id_equipo === idEquipo)}
            deshabilitado={bloqueado}
            agregar={(cis, texto) =>
              accion(() => post(`/partidos/${id}/planilla`, { ci_jugadores: cis }), texto)
            }
            quitar={(j) => accion(() => del(`/partidos/${id}/planilla/${j.ci}`), `${nombreCompleto(j)} quitado de la planilla`)}
          />
        ))}
      </div>

      <div className="columnas iguales">
        <section className="tarjeta">
          <h2>Goles</h2>
          <Tabla
            filas={partido.goles}
            clave={(g) => g.id_gol}
            vacio="Sin goles registrados"
            columnas={[
              { campo: "minuto", titulo: "Min", alinear: "centro", render: (g) => `${g.minuto}'` },
              { campo: "jugador", titulo: "Jugador", render: nombreCompleto },
              {
                campo: "equipo",
                titulo: "Equipo",
                render: (g) => (
                  <>
                    {nombreEquipo(g.id_equipo)} {g.autogol ? <span className="etiqueta et-autogol">en contra</span> : null}
                  </>
                ),
              },
            ]}
            acciones={
              bloqueado
                ? null
                : (g) => (
                    <button
                      className="boton peligro chico"
                      onClick={() => window.confirm("¿Eliminar el gol?") && accion(() => del(`/partidos/${id}/goles/${g.id_gol}`), "Gol eliminado")}
                    >
                      Eliminar
                    </button>
                  )
            }
          />
          {!bloqueado && (
            <FormularioEvento
              claveForm={claveGol}
              opcionesPlanilla={opcionesPlanilla}
              textoBoton="Registrar gol"
              extra={[{ nombre: "autogol", etiqueta: "Autogol", tipo: "checkbox" }]}
              onSubmit={registrarGol}
            />
          )}
        </section>

        <section className="tarjeta">
          <h2>Tarjetas</h2>
          <Tabla
            filas={partido.tarjetas}
            clave={(t) => t.id_tarjeta}
            vacio="Sin tarjetas registradas"
            columnas={[
              { campo: "minuto", titulo: "Min", alinear: "centro", render: (t) => `${t.minuto}'` },
              { campo: "jugador", titulo: "Jugador", render: nombreCompleto },
              { campo: "equipo", titulo: "Equipo", render: (t) => nombreEquipo(t.id_equipo) },
              { campo: "color", titulo: "Tarjeta", render: (t) => <Etiqueta valor={t.color} /> },
            ]}
            acciones={
              bloqueado
                ? null
                : (t) => (
                    <button
                      className="boton peligro chico"
                      onClick={() =>
                        window.confirm("¿Eliminar la tarjeta? Si generó una sanción, también se elimina.") &&
                        accion(() => del(`/partidos/${id}/tarjetas/${t.id_tarjeta}`), "Tarjeta eliminada")
                      }
                    >
                      Eliminar
                    </button>
                  )
            }
          />
          {!bloqueado && (
            <FormularioEvento
              claveForm={claveTarjeta}
              opcionesPlanilla={opcionesPlanilla}
              textoBoton="Registrar tarjeta"
              extra={[
                {
                  nombre: "color",
                  etiqueta: "Color",
                  tipo: "select",
                  requerido: true,
                  defecto: "amarilla",
                  opciones: [
                    { valor: "amarilla", etiqueta: "Amarilla" },
                    { valor: "roja", etiqueta: "Roja" },
                  ],
                },
              ]}
              onSubmit={registrarTarjeta}
            />
          )}
        </section>
      </div>
    </>
  );
}

function explicacion(partido, noDisputado, plazoVencido) {
  if (["postergado", "cancelado"].includes(partido.estado)) return `El partido está ${partido.estado}: no admite planilla.`;
  if (noDisputado) return "El partido todavía no se disputó: la planilla se habilita cuando termine su turno.";
  if (plazoVencido) return "Pasaron más de 48 horas desde el partido: la planilla es de solo lectura.";
  if (partido.estado === "jugado") return "El partido está jugado: la planilla puede corregirse hasta 48 horas después.";
  return "Cargue la planilla, los goles y las tarjetas, y luego marque el partido como jugado.";
}

// Antes de marcarlo como jugado, el marcador se calcula con los goles cargados
function golesParciales(partido) {
  if (!partido.goles.length) return "vs";
  let local = 0;
  let visitante = 0;
  for (const g of partido.goles) {
    const delLocal = g.id_equipo === partido.id_equipo_local;
    if (delLocal !== !!g.autogol) local++;
    else visitante++;
  }
  return `${local} – ${visitante}`;
}

function PlantelEquipo({ nombre, jugadores, deshabilitado, agregar, quitar }) {
  const habilitados = jugadores.filter((j) => !j.en_planilla && !j.suspendido);
  const enPlanilla = jugadores.filter((j) => j.en_planilla).length;

  return (
    <section className="tarjeta">
      <div className="encabezado">
        <div>
          <h2>{nombre}</h2>
          <p className="apagado">{enPlanilla} en la planilla</p>
        </div>
        {!deshabilitado && habilitados.length > 0 && (
          <button
            className="boton secundario chico"
            onClick={() => agregar(habilitados.map((j) => j.ci), `${habilitados.length} jugador(es) agregados`)}
          >
            Agregar todos los habilitados
          </button>
        )}
      </div>
      <ul className="lista-planilla">
        {jugadores.map((j) => (
          <li key={j.ci} className={j.en_planilla ? "en-planilla" : ""}>
            <span className="camiseta">{j.numero_camiseta}</span>
            <span className="nombre">{nombreCompleto(j)}</span>
            {j.suspendido ? (
              <span className="etiqueta et-suspendido">Suspendido</span>
            ) : deshabilitado ? null : j.en_planilla ? (
              <button className="boton peligro chico" onClick={() => quitar(j)}>
                Quitar
              </button>
            ) : (
              <button className="boton secundario chico" onClick={() => agregar([j.ci], `${nombreCompleto(j)} agregado a la planilla`)}>
                Agregar
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function FormularioEvento({ claveForm, opcionesPlanilla, textoBoton, extra, onSubmit }) {
  if (!opcionesPlanilla.length) {
    return <p className="nota">Primero agregue jugadores a la planilla.</p>;
  }
  return (
    <Formulario
      key={claveForm}
      enLinea
      textoBoton={textoBoton}
      campos={[
        { nombre: "ci_jugador", etiqueta: "Jugador", tipo: "select", numero: true, requerido: true, opciones: opcionesPlanilla },
        { nombre: "minuto", etiqueta: "Minuto", tipo: "number", requerido: true, min: 0, max: 60 },
        ...extra,
      ]}
      onSubmit={onSubmit}
    />
  );
}
