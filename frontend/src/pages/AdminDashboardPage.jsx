import { Link } from "react-router-dom";
import { getSessionFarmer } from "../api/client";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

export default function AdminDashboardPage() {
  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">PMV3 · Administración</p>
        <h1>Panel administrativo</h1>
        <p className="lead">Bienvenido, {getSessionFarmer() || "Administrador"}. Gestiona el conocimiento y revisa el funcionamiento del sistema.</p>
        <div className="panel-links">
          <Link to="/admin/documents"><strong>Documentos agrícolas</strong><p>Registrar, actualizar y deshabilitar contenido de la base de conocimiento.</p></Link>
          <Link to="/admin/metrics"><strong>Indicadores de calidad</strong><p>Revisar consultas atendidas y tiempos de respuesta por periodo.</p></Link>\n          <Link to="/admin/evaluations"><strong>Evaluación de IA</strong><p>Consultar comparaciones de evaluaciones RAGAS ejecutadas por el equipo.</p></Link>
        </div>
      </section>
    </AuthenticatedShell>
  );
}
