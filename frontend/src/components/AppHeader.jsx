import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { clearSession, getSessionRole } from "../api/client";
import BrandMark from "./BrandMark.jsx";

export default function AppHeader() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const isAdmin = getSessionRole() === "ADMINISTRADOR";

  function handleLogout() {
    clearSession();
    navigate(isAdmin ? "/admin/login" : "/login", { replace: true });
  }

  function closeMenu() {
    setOpen(false);
  }

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <NavLink to={isAdmin ? "/admin" : "/dashboard"} className="brand-link" onClick={closeMenu}>
          <BrandMark />
        </NavLink>
        <button
          type="button"
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="app-navigation"
          onClick={() => setOpen((current) => !current)}
        >
          Menú
        </button>
        <nav id="app-navigation" className={`site-nav ${open ? "is-open" : ""}`} aria-label="Navegación principal">
          {isAdmin ? (
            <>
              <NavLink to="/admin" onClick={closeMenu}>Panel</NavLink>
              <NavLink to="/admin/documents" onClick={closeMenu}>Documentos</NavLink>
              <NavLink to="/admin/metrics" onClick={closeMenu}>Indicadores</NavLink>
              <NavLink to="/admin/evaluations" onClick={closeMenu}>Evaluación IA</NavLink>
            </>
          ) : (
            <>
              <NavLink to="/dashboard" onClick={closeMenu}>Panel</NavLink>
              <NavLink to="/context" onClick={closeMenu}>Contexto agrícola</NavLink>
              <NavLink to="/query" onClick={closeMenu}>Consulta</NavLink>
              <NavLink to="/riesgo" onClick={closeMenu}>Riesgo experimental</NavLink>
            </>
          )}
          <button type="button" className="logout-button logout-button-header" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </nav>
      </div>
    </header>
  );
}
