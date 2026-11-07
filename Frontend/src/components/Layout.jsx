import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useTorneo } from "../context/TorneoContext.jsx";

const MENU = [
  { ruta: "/", texto: "Inicio", soloAdmin: false },
  { ruta: "/partidos", texto: "Partidos", soloAdmin: false },
  { ruta: "/equipos", texto: "Equipos y planteles", soloAdmin: true },
  { ruta: "/jugadores", texto: "Jugadores", soloAdmin: true },
  { ruta: "/sanciones", texto: "Sanciones", soloAdmin: true },
  { ruta: "/torneos", texto: "Torneos", soloAdmin: true },
  { ruta: "/complejos", texto: "Complejos y canchas", soloAdmin: true },
  { ruta: "/facultades", texto: "Facultades", soloAdmin: true },
  { ruta: "/reportes", texto: "Reportes", soloAdmin: false },
];

export default function Layout({ children }) {
  const { sesion, esAdmin, logout } = useAuth();
  const { torneos, torneo, seleccionar } = useTorneo();
  const [menuAbierto, setMenuAbierto] = useState(false);

  return (
    <div className={`app ${menuAbierto ? "menu-abierto" : ""}`}>
      <aside className="lateral">
        <div className="marca">
          <span className="marca-icono" aria-hidden="true">⚽</span>
          <div>
            <strong>Fútbol 5</strong>
            <small>Interfacultades UCU</small>
          </div>
        </div>
        <nav>
          {MENU.filter((m) => esAdmin || !m.soloAdmin).map((m) => (
            <NavLink key={m.ruta} to={m.ruta} end={m.ruta === "/"} onClick={() => setMenuAbierto(false)}>
              {m.texto}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="principal">
        <header className="barra">
          <button className="boton-menu" onClick={() => setMenuAbierto((v) => !v)} aria-label="Abrir menú">
            ☰
          </button>
          <label className="selector-torneo">
            <span>Edición</span>
            <select
              value={torneo?.id_torneo ?? ""}
              onChange={(e) => seleccionar(Number(e.target.value))}
              disabled={!torneos.length}
            >
              {!torneos.length && <option value="">Sin torneos</option>}
              {torneos.map((t) => (
                <option key={t.id_torneo} value={t.id_torneo}>
                  {t.nombre} ({t.estado})
                </option>
              ))}
            </select>
          </label>
          <div className="usuario">
            <span>
              {sesion.correo}
              <small>{sesion.rol}</small>
            </span>
            <button className="boton secundario chico" onClick={logout}>
              Salir
            </button>
          </div>
        </header>
        <main className="contenido">{children}</main>
      </div>
      <div className="velo" onClick={() => setMenuAbierto(false)} />
    </div>
  );
}
