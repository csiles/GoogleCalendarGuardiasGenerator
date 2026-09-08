import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { GeneratorPage } from "./pages/GeneratorPage";
import { ViewerPage } from "./pages/ViewerPage";

export function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Gestión de Guardias - Soporte IT-Leisure</h1>
        <nav className="tabs">
          <NavLink to="/generador" className={({ isActive }) => `tab-link${isActive ? " active" : ""}`}>
            Generar Guardias
          </NavLink>
          <NavLink to="/visualizador" className={({ isActive }) => `tab-link${isActive ? " active" : ""}`}>
            Ver Calendarios
          </NavLink>
        </nav>
      </header>
      <main className="app-content">
        <Routes>
          <Route path="/" element={<Navigate to="/generador" replace />} />
          <Route path="/generador" element={<GeneratorPage />} />
          <Route path="/visualizador" element={<ViewerPage />} />
        </Routes>
      </main>
    </div>
  );
}
