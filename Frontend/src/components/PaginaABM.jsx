import { useState } from "react";
import { useAviso } from "../context/AvisoContext.jsx";
import { useCarga } from "../util.js";
import Formulario from "./Formulario.jsx";
import Modal from "./Modal.jsx";
import Tabla from "./Tabla.jsx";

/**
 * Pantalla de Alta, Baja y Modificación reutilizable.
 * - cargar(): promesa con las filas; deps: cuándo volver a cargar
 * - campos: lista de campos, o función (modo, fila) => campos  (modo: "alta" | "edicion")
 * - crear(valores), modificar(fila, valores), eliminar(fila): llamadas a la API (opcionales)
 * - acciones(fila, recargar): botones extra por fila
 * - buscar(fila): texto donde busca el cuadro de búsqueda
 * - alCambiar(): se llama después de cada alta, baja o modificación exitosa
 */
export default function PaginaABM({
  titulo,
  subtitulo,
  cargar,
  deps = [],
  columnas,
  clave,
  campos,
  valoresEdicion,
  crear,
  modificar,
  eliminar,
  describir,
  acciones,
  buscar,
  alCambiar,
  textoNuevo = "Nuevo",
  aviso: avisoSuperior,
  vacio,
  nivel = "pagina",
}) {
  const aviso = useAviso();
  const { datos, error, cargando, recargar } = useCarga(cargar, deps);
  const [modal, setModal] = useState(null);
  const [texto, setTexto] = useState("");

  const filas = (datos || []).filter(
    (f) => !texto || !buscar || buscar(f).toLowerCase().includes(texto.toLowerCase())
  );

  const listo = () => {
    recargar();
    alCambiar?.();
  };

  const guardar = async (valores) => {
    if (modal.modo === "alta") {
      await crear(valores);
      aviso.ok("Registro creado");
    } else {
      await modificar(modal.fila, valores);
      aviso.ok("Cambios guardados");
    }
    setModal(null);
    listo();
  };

  const borrar = async (fila) => {
    const nombre = describir ? describir(fila) : "este registro";
    if (!window.confirm(`¿Eliminar ${nombre}?`)) return;
    try {
      await eliminar(fila);
      aviso.ok("Registro eliminado");
      listo();
    } catch (e) {
      aviso.error(e.message);
    }
  };

  const camposModal = modal ? (typeof campos === "function" ? campos(modal.modo, modal.fila) : campos) : [];
  const Titulo = nivel === "pagina" ? "h1" : "h2";

  return (
    <section className={nivel === "pagina" ? "" : "tarjeta"}>
      <div className="encabezado">
        <div>
          <Titulo>{titulo}</Titulo>
          {subtitulo && <p className="apagado">{subtitulo}</p>}
        </div>
        <div className="herramientas">
          {buscar && (
            <input
              className="buscador"
              type="search"
              placeholder="Buscar…"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
            />
          )}
          {crear && (
            <button className="boton" onClick={() => setModal({ modo: "alta", fila: null })}>
              + {textoNuevo}
            </button>
          )}
        </div>
      </div>

      {avisoSuperior}
      {error && <p className="error">{error}</p>}

      <Tabla
        columnas={columnas}
        filas={filas}
        clave={clave}
        cargando={cargando}
        vacio={vacio}
        acciones={
          acciones || modificar || eliminar
            ? (fila) => (
                <>
                  {acciones?.(fila, listo)}
                  {modificar && (
                    <button className="boton secundario chico" onClick={() => setModal({ modo: "edicion", fila })}>
                      Editar
                    </button>
                  )}
                  {eliminar && (
                    <button className="boton peligro chico" onClick={() => borrar(fila)}>
                      Eliminar
                    </button>
                  )}
                </>
              )
            : null
        }
      />

      {modal && (
        <Modal titulo={modal.modo === "alta" ? `${textoNuevo}` : `Editar`} onClose={() => setModal(null)}>
          <Formulario
            campos={camposModal}
            inicial={modal.fila ? (valoresEdicion ? valoresEdicion(modal.fila) : modal.fila) : {}}
            onSubmit={guardar}
            onCancel={() => setModal(null)}
          />
        </Modal>
      )}
    </section>
  );
}
