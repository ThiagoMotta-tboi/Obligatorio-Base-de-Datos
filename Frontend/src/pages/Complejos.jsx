import { useState } from "react";
import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import PaginaABM from "../components/PaginaABM.jsx";
import { SUPERFICIES, opciones, opcionesTexto, useCarga } from "../util.js";

export default function Complejos() {
  // Cambia cada vez que se modifica un complejo, para refrescar la lista de canchas
  const [version, setVersion] = useState(0);
  const { datos: complejos } = useCarga(() => get("/complejos"), [version]);
  const refrescar = () => setVersion((v) => v + 1);

  return (
    <>
      <h1>Complejos y canchas</h1>
      <div className="pila">
        <PaginaABM
          nivel="seccion"
          titulo="Complejos deportivos"
          textoNuevo="Nuevo complejo"
          cargar={() => get("/complejos")}
          deps={[version]}
          clave={(c) => c.id_complejo}
          columnas={[
            { campo: "nombre", titulo: "Nombre" },
            { campo: "direccion", titulo: "Dirección" },
            { campo: "departamento", titulo: "Departamento" },
            { campo: "canchas", titulo: "Canchas", alinear: "centro" },
          ]}
          campos={[
            { nombre: "nombre", etiqueta: "Nombre", requerido: true },
            { nombre: "direccion", etiqueta: "Dirección", requerido: true },
            { nombre: "departamento", etiqueta: "Departamento", requerido: true, defecto: "Montevideo" },
          ]}
          crear={(v) => post("/complejos", v)}
          modificar={(c, v) => put(`/complejos/${c.id_complejo}`, v)}
          eliminar={(c) => del(`/complejos/${c.id_complejo}`)}
          describir={(c) => `el complejo ${c.nombre}`}
          alCambiar={refrescar}
        />

        <PaginaABM
          nivel="seccion"
          titulo="Canchas"
          textoNuevo="Nueva cancha"
          cargar={() => get("/canchas")}
          deps={[version]}
          clave={(c) => `${c.id_complejo}-${c.nombre_cancha}`}
          columnas={[
            { campo: "complejo", titulo: "Complejo" },
            { campo: "nombre_cancha", titulo: "Cancha" },
            { campo: "superficie", titulo: "Superficie", render: (c) => <Etiqueta valor={c.superficie} /> },
            { campo: "techada", titulo: "Techada", alinear: "centro", render: (c) => (c.techada ? "Sí" : "No") },
          ]}
          campos={(modo) => [
            ...(modo === "alta"
              ? [
                  {
                    nombre: "id_complejo",
                    etiqueta: "Complejo",
                    tipo: "select",
                    numero: true,
                    requerido: true,
                    opciones: opciones(complejos, "id_complejo", "nombre"),
                  },
                  { nombre: "nombre_cancha", etiqueta: "Nombre de la cancha", requerido: true },
                ]
              : []),
            { nombre: "superficie", etiqueta: "Superficie", tipo: "select", requerido: true, opciones: opcionesTexto(SUPERFICIES) },
            { nombre: "techada", etiqueta: "Techada", tipo: "checkbox" },
          ]}
          crear={({ id_complejo, ...resto }) => post(`/complejos/${id_complejo}/canchas`, resto)}
          modificar={(c, v) => put(`/complejos/${c.id_complejo}/canchas/${encodeURIComponent(c.nombre_cancha)}`, v)}
          eliminar={(c) => del(`/complejos/${c.id_complejo}/canchas/${encodeURIComponent(c.nombre_cancha)}`)}
          describir={(c) => `la ${c.nombre_cancha} de ${c.complejo}`}
          alCambiar={refrescar}
        />
      </div>
    </>
  );
}
