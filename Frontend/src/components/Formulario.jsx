import { useState } from "react";

/**
 * Formulario generado a partir de una lista de campos.
 * campo: { nombre, etiqueta, tipo?: "text"|"number"|"date"|"email"|"password"|"select"|"checkbox",
 *          opciones?: [{ valor, etiqueta }], requerido?, numero? (select numérico), defecto?, min?, max?, ayuda? }
 * onSubmit recibe los valores ya convertidos; si lanza un error, se muestra en el formulario.
 */
export default function Formulario({ campos, inicial = {}, onSubmit, onCancel, textoBoton = "Guardar", enLinea = false }) {
  const [valores, setValores] = useState(() => valoresIniciales(campos, inicial));
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  const cambiar = (nombre, valor) => setValores((v) => ({ ...v, [nombre]: valor }));

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await onSubmit(convertir(campos, valores));
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form className={enLinea ? "formulario en-linea" : "formulario"} onSubmit={enviar}>
      <div className="campos">
        {campos.map((c) => (
          <Campo key={c.nombre} campo={c} valor={valores[c.nombre]} onChange={(v) => cambiar(c.nombre, v)} />
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      <div className="botonera">
        {onCancel && (
          <button type="button" className="boton secundario" onClick={onCancel}>
            Cancelar
          </button>
        )}
        <button type="submit" className="boton" disabled={enviando}>
          {enviando ? "Guardando…" : textoBoton}
        </button>
      </div>
    </form>
  );
}

function Campo({ campo, valor, onChange }) {
  const id = `campo-${campo.nombre}`;

  if (campo.tipo === "checkbox") {
    return (
      <label className="campo-check">
        <input type="checkbox" checked={!!valor} onChange={(e) => onChange(e.target.checked)} />
        {campo.etiqueta}
      </label>
    );
  }

  return (
    <div className="campo">
      <label htmlFor={id}>
        {campo.etiqueta}
        {campo.requerido && <span className="obligatorio"> *</span>}
      </label>
      {campo.tipo === "select" ? (
        <select id={id} value={valor ?? ""} onChange={(e) => onChange(e.target.value)} required={campo.requerido}>
          <option value="">Seleccionar…</option>
          {campo.opciones.map((o) => (
            <option key={o.valor} value={o.valor}>
              {o.etiqueta}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          type={campo.tipo || "text"}
          value={valor ?? ""}
          onChange={(e) => onChange(e.target.value)}
          required={campo.requerido}
          min={campo.min}
          max={campo.max}
          step={campo.tipo === "number" ? 1 : undefined}
        />
      )}
      {campo.ayuda && <small>{campo.ayuda}</small>}
    </div>
  );
}

function valoresIniciales(campos, inicial) {
  const valores = {};
  for (const c of campos) {
    const v = inicial[c.nombre] ?? c.defecto;
    valores[c.nombre] = c.tipo === "checkbox" ? !!v : v ?? "";
  }
  return valores;
}

function convertir(campos, valores) {
  const resultado = {};
  for (const c of campos) {
    let v = valores[c.nombre];
    if (c.tipo === "checkbox") v = !!v;
    else if (v === "" || v == null) v = null;
    else if (c.tipo === "number" || c.numero) v = Number(v);
    resultado[c.nombre] = v;
  }
  return resultado;
}
