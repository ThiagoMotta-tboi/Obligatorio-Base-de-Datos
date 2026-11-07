# Frontend – Torneo Interfacultades de Fútbol 5

Aplicación web en React (Vite). Consume la API del backend; en desarrollo, las llamadas a `/api`
se reenvían a `http://127.0.0.1:5000` (ver `vite.config.js`).

## Puesta en marcha

Con el backend corriendo (`python app.py` en la carpeta `Backend`), desde `Frontend`:

```powershell
npm install
npm run dev
```

Abrir `http://localhost:5173` e ingresar con un usuario creado con `Backend/crear_usuario.py`.

## Pantallas

| Pantalla | Rol | Qué permite |
|---|---|---|
| Inicio | Ambos | Resumen de la edición, tabla de posiciones, próximos partidos y planillas pendientes |
| Partidos | Ambos | Fixture con filtros. El administrador programa, reprograma, posterga, cancela y elimina |
| Planilla de un partido | Ambos | Planilla de juego, goles y tarjetas; marcar el partido como jugado |
| Reportes | Ambos | Los 10 reportes pedidos y los 3 propuestos |
| Equipos y planteles | Administrador | ABM de equipos, plantel, camisetas y capitán |
| Jugadores | Administrador | ABM de jugadores con búsqueda |
| Sanciones | Administrador | ABM de sanciones (las automáticas aparecen como tales) |
| Torneos | Administrador | ABM de ediciones y avance de etapa |
| Complejos y canchas | Administrador | ABM de complejos y sus canchas |
| Facultades | Administrador | ABM de facultades |

El selector "Edición" de la barra superior elige el torneo con el que trabajan las pantallas.

## Estructura

| Carpeta / archivo | Contenido |
|---|---|
| `src/api.js` | Cliente HTTP: agrega el token y traduce los errores del backend |
| `src/context/` | Sesión (`AuthContext`), edición seleccionada (`TorneoContext`) y avisos |
| `src/components/` | Piezas reutilizables: `PaginaABM`, `Tabla`, `Formulario`, `Modal` |
| `src/pages/` | Una pantalla por sección |
