import { Link } from "react-router-dom";
import PublicShell from "../components/PublicShell.jsx";

export default function NotFoundPage() {
  return (
    <PublicShell>
      <section className="card">
        <p className="eyebrow">Error 404</p>
        <h1>Página no encontrada</h1>
        <p className="lead">
          La ruta solicitada no existe en Agro Asistente. Comprueba la dirección o vuelve
          al inicio.
        </p>
        <div className="hero-actions">
          <Link className="button" to="/">Ir al inicio</Link>
          <Link className="button button-secondary" to="/login">Iniciar sesión</Link>
        </div>
      </section>
    </PublicShell>
  );
}
