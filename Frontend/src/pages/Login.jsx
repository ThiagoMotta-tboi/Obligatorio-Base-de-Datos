import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await login(correo, password);
    } catch (err) {
      setError(err.message);
      setEnviando(false);
    }
  };

  return (
    <div className="login">
      <form className="login-caja" onSubmit={enviar}>
        <div className="login-marca">
          <span aria-hidden="true">⚽</span>
          <h1>Torneo Interfacultades</h1>
          <p className="apagado">Fútbol 5 · Universidad Católica del Uruguay</p>
        </div>
        <div className="campo">
          <label htmlFor="correo">Correo</label>
          <input id="correo" type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} required autoFocus />
        </div>
        <div className="campo">
          <label htmlFor="password">Contraseña</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="error">{error}</p>}
        <button className="boton ancho" disabled={enviando}>
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
