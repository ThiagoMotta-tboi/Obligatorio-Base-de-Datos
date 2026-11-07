import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { AvisoProvider } from "./context/AvisoContext.jsx";
import { TorneoProvider } from "./context/TorneoContext.jsx";
import "./estilos.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AvisoProvider>
        <AuthProvider>
          <TorneoProvider>
            <App />
          </TorneoProvider>
        </AuthProvider>
      </AvisoProvider>
    </BrowserRouter>
  </React.StrictMode>
);
