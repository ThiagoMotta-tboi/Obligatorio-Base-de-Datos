import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import Formulario from "../components/Formulario.jsx";
import Tabla from "../components/Tabla.jsx";
import { useAviso } from "../context/AvisoContext.jsx";
import { nombreCompleto, useCarga } from "../util.js";

export default function EquipoDetalle() {
  const { id } = useParams();
  const aviso = useAviso();
  const [claveForm, setClaveForm] = useState(0);
  const { datos, error, recargar } = useCarga(
    () => Promise.all([get(`/equipos/${id}`), get(`/equipos/${id}/disponibles`)]),
    [id]
  );

  if (error) return <p className="error">{error}</p>;
  if (!datos) return <p className="apagado">Cargando…</p>;

  const [equipo, disponibles] = datos;
  const editable = equipo.estado_torneo === "inscripcion";
  const plantel = equipo.plantel;
  const docentes = plantel.filter((j) => ["docente", "funcionario"].includes(j.tipo)).length;

  const accion = async (fn, mensaje) => {
    try {
      await fn();
      aviso.ok(mensaje);
      await recargar();
    } catch (e) {
      aviso.error(e.message);
    }
  };

  const hacerCapitan = (j) =>
    accion(
      () => put(`/equipos/${id}`, { nombre: equipo.nombre, id_facultad: equipo.id_facultad, ci_capitan: j.ci }),
      `${nombreCompleto(j)} es el nuevo capitán`
    );

  const cambiarCamiseta = (j) => {
    const numero = window.prompt(`Nuevo número de camiseta para ${nombreCompleto(j)}`, j.numero_camiseta);
    if (!numero) return;
    accion(() => put(`/equipos/${id}/jugadores/${j.ci}`, { numero_camiseta: Number(numero) }), "Camiseta actualizada");
  };

  const quitar = (j) => {
    if (!window.confirm(`¿Quitar a ${nombreCompleto(j)} del plantel?`)) return;
    accion(() => del(`/equipos/${id}/jugadores/${j.ci}`), "Jugador quitado del plantel");
  };

  const agregar = async (v) => {
    await post(`/equipos/${id}/jugadores`, v);
    aviso.ok("Jugador agregado al plantel");
    setClaveForm((k) => k + 1);
    await recargar();
  };

  // Primer número de camiseta libre, como sugerencia
  const usados = new Set(plantel.map((j) => j.numero_camiseta));
  let sugerido = 1;
  while (usados.has(sugerido)) sugerido++;

  return (
    <>
      <Link to="/equipos" className="volver">
        ← Equipos
      </Link>
      <div className="encabezado">
        <div>
          <h1>{equipo.nombre}</h1>
          <p className="apagado">
            {equipo.facultad} · {equipo.torneo}
          </p>
        </div>
        <Etiqueta valor={equipo.estado_torneo} />
      </div>

      <div className="indicadores">
        <div className={`indicador ${plantel.length < 5 ? "alerta" : ""}`}>
          <strong>{plantel.length} / 10</strong>
          <span>Jugadores (mínimo 5)</span>
        </div>
        <div className="indicador">
          <strong>{docentes} / 2</strong>
          <span>Docentes y funcionarios</span>
        </div>
        <div className={`indicador ${equipo.ci_capitan ? "" : "alerta"}`}>
          <strong>{plantel.find((j) => j.es_capitan) ? nombreCompleto(plantel.find((j) => j.es_capitan)) : "—"}</strong>
          <span>Capitán</span>
        </div>
      </div>

      {!editable && (
        <p className="nota">
          El torneo está <strong>{equipo.estado_torneo}</strong>: el plantel ya no puede modificarse. Solo se puede cambiar el capitán.
        </p>
      )}

      <section className="tarjeta">
        <h2>Plantel</h2>
        <Tabla
          filas={plantel}
          clave={(j) => j.ci}
          vacio="El plantel está vacío"
          columnas={[
            { campo: "numero_camiseta", titulo: "N.º", alinear: "centro" },
            {
              campo: "nombre",
              titulo: "Jugador",
              render: (j) => (
                <>
                  {nombreCompleto(j)} {j.es_capitan ? <span className="etiqueta et-capitan">Capitán</span> : null}
                </>
              ),
            },
            { campo: "ci", titulo: "Cédula" },
            { campo: "tipo", titulo: "Tipo", render: (j) => <Etiqueta valor={j.tipo} /> },
          ]}
          acciones={(j) => (
            <>
              {!j.es_capitan && (
                <button className="boton secundario chico" onClick={() => hacerCapitan(j)}>
                  Hacer capitán
                </button>
              )}
              {editable && (
                <>
                  <button className="boton secundario chico" onClick={() => cambiarCamiseta(j)}>
                    Camiseta
                  </button>
                  <button className="boton peligro chico" onClick={() => quitar(j)}>
                    Quitar
                  </button>
                </>
              )}
            </>
          )}
        />
      </section>

      {editable && (
        <section className="tarjeta">
          <h2>Agregar jugador</h2>
          {disponibles.length ? (
            <Formulario
              key={claveForm}
              enLinea
              textoBoton="Agregar al plantel"
              inicial={{ numero_camiseta: sugerido }}
              campos={[
                {
                  nombre: "ci_jugador",
                  etiqueta: "Jugador",
                  tipo: "select",
                  numero: true,
                  requerido: true,
                  opciones: disponibles.map((j) => ({ valor: j.ci, etiqueta: `${nombreCompleto(j)} (${j.tipo})` })),
                },
                { nombre: "numero_camiseta", etiqueta: "Camiseta", tipo: "number", requerido: true, min: 1, max: 99 },
              ]}
              onSubmit={agregar}
            />
          ) : (
            <p className="vacio">No hay jugadores de {equipo.facultad} disponibles en esta edición.</p>
          )}
        </section>
      )}
    </>
  );
}
