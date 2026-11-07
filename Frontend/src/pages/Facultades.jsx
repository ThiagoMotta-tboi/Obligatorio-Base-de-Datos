import { del, get, post, put } from "../api.js";
import PaginaABM from "../components/PaginaABM.jsx";

export default function Facultades() {
  return (
    <PaginaABM
      titulo="Facultades"
      textoNuevo="Nueva facultad"
      cargar={() => get("/facultades")}
      clave={(f) => f.id_facultad}
      columnas={[{ campo: "nombre", titulo: "Nombre" }]}
      campos={[{ nombre: "nombre", etiqueta: "Nombre", requerido: true }]}
      crear={(v) => post("/facultades", v)}
      modificar={(f, v) => put(`/facultades/${f.id_facultad}`, v)}
      eliminar={(f) => del(`/facultades/${f.id_facultad}`)}
      describir={(f) => `la facultad ${f.nombre}`}
    />
  );
}
