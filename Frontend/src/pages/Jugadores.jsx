import { del, get, post, put } from "../api.js";
import Etiqueta from "../components/Etiqueta.jsx";
import PaginaABM from "../components/PaginaABM.jsx";
import { TIPOS_JUGADOR, fmtFecha, nombreCompleto, opciones, opcionesTexto, useCarga } from "../util.js";

export default function Jugadores() {
  const { datos: facultades } = useCarga(() => get("/facultades"), []);

  const campos = (modo) => [
    ...(modo === "alta" ? [{ nombre: "ci", etiqueta: "Cédula", tipo: "number", requerido: true, min: 1 }] : []),
    { nombre: "nombre", etiqueta: "Nombre", requerido: true },
    { nombre: "apellido", etiqueta: "Apellido", requerido: true },
    { nombre: "email", etiqueta: "Email", tipo: "email", requerido: true },
    { nombre: "fecha_nacimiento", etiqueta: "Fecha de nacimiento", tipo: "date", requerido: true },
    {
      nombre: "id_facultad",
      etiqueta: "Facultad",
      tipo: "select",
      numero: true,
      requerido: true,
      opciones: opciones(facultades, "id_facultad", "nombre"),
      ayuda: modo === "edicion" ? "No puede cambiarse si el jugador integra un plantel" : undefined,
    },
    { nombre: "tipo", etiqueta: "Tipo", tipo: "select", requerido: true, opciones: opcionesTexto(TIPOS_JUGADOR) },
  ];

  return (
    <PaginaABM
      titulo="Jugadores"
      subtitulo="Estudiantes de grado y posgrado, docentes y funcionarios"
      textoNuevo="Nuevo jugador"
      cargar={() => get("/jugadores")}
      clave={(j) => j.ci}
      buscar={(j) => `${j.ci} ${nombreCompleto(j)} ${j.facultad} ${j.tipo}`}
      columnas={[
        { campo: "ci", titulo: "Cédula" },
        { campo: "nombre", titulo: "Nombre", render: nombreCompleto },
        { campo: "email", titulo: "Email" },
        { campo: "fecha_nacimiento", titulo: "Nacimiento", render: (j) => fmtFecha(j.fecha_nacimiento) },
        { campo: "facultad", titulo: "Facultad" },
        { campo: "tipo", titulo: "Tipo", render: (j) => <Etiqueta valor={j.tipo} /> },
      ]}
      campos={campos}
      crear={(v) => post("/jugadores", v)}
      modificar={(j, v) => put(`/jugadores/${j.ci}`, v)}
      eliminar={(j) => del(`/jugadores/${j.ci}`)}
      describir={(j) => `a ${nombreCompleto(j)}`}
    />
  );
}
