import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { urlBaseApi } from "../api/baseUrl.js";
import { getHealth } from "../api/client";
import { destinoHealth, mensajeErrorConexion } from "../api/conexion.js";
import PublicShell from "../components/PublicShell.jsx";

export default function HomePage() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then((response) => {
        setHealth(response.data);
        setError("");
      })
      .catch((error) => {
        const destino = destinoHealth(urlBaseApi(import.meta.env));
        setError(mensajeErrorConexion(error, destino));
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <PublicShell>
      <section className="card">
        <h1>Agro-Asistente</h1>
        <p className="lead">Plataforma de asistencia técnica agrícola</p>
        <p className="lead">
          Permite registrar un contexto de cultivo, consultar asistencia técnica
          y revisar la base de conocimiento disponible.
        </p>

        <div className="hero-actions">
          <Link className="button" to="/login">Iniciar sesión</Link>
          <Link className="button button-secondary" to="/register">Crear cuenta</Link>
        </div>

        <div className={`status tech-status ${error ? "status-error" : "status-ok"}`}>
          {loading && <p>Comprobando disponibilidad del servicio…</p>}
          {!loading && error && <p>{error}</p>}
          {!loading && health && (
            <p>
              Servicio{" "}
              {health.status === "ok" ? "disponible" : "con incidencias"}
              {health.mysql === "connected"
                ? " · base de datos conectada"
                : health.mysql
                  ? " · base de datos no disponible"
                  : ""}
              .
            </p>
          )}
        </div>
      </section>
    </PublicShell>
  );
}
