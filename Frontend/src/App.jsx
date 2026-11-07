import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import Complejos from "./pages/Complejos.jsx";
import EquipoDetalle from "./pages/EquipoDetalle.jsx";
import Equipos from "./pages/Equipos.jsx";
import Facultades from "./pages/Facultades.jsx";
import Inicio from "./pages/Inicio.jsx";
import Jugadores from "./pages/Jugadores.jsx";
import Login from "./pages/Login.jsx";
import PartidoPlanilla from "./pages/PartidoPlanilla.jsx";
import Partidos from "./pages/Partidos.jsx";
import Reportes from "./pages/Reportes.jsx";
import Sanciones from "./pages/Sanciones.jsx";
import Torneos from "./pages/Torneos.jsx";

export default function App() {
  const { sesion, esAdmin } = useAuth();
  if (!sesion) return <Login />;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/partidos" element={<Partidos />} />
        <Route path="/partidos/:id" element={<PartidoPlanilla />} />
        <Route path="/reportes" element={<Reportes />} />
        {esAdmin && (
          <>
            <Route path="/torneos" element={<Torneos />} />
            <Route path="/equipos" element={<Equipos />} />
            <Route path="/equipos/:id" element={<EquipoDetalle />} />
            <Route path="/jugadores" element={<Jugadores />} />
            <Route path="/facultades" element={<Facultades />} />
            <Route path="/complejos" element={<Complejos />} />
            <Route path="/sanciones" element={<Sanciones />} />
          </>
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
