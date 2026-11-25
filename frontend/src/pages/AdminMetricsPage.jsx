import { useEffect, useState } from "react";
import { getAdminMetrics } from "../api/client";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

export default function AdminMetricsPage() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    getAdminMetrics(days)
      .then((response) => { if (active) setData(response.data); })
      .catch(() => { if (active) setError("No se pudieron cargar los indicadores."); });
    return () => { active = false; };
  }, [days]);

  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">HU-15</p>
        <h1>Indicadores de funcionamiento</h1>
        <p className="lead">Valores calculados con las solicitudes recibidas por el servicio de consultas.</p>
        <label htmlFor="metrics-period">Periodo</label>
        <select id="metrics-period" value={days} onChange={(event) => setDays(Number(event.target.value))}>
          <option value={7}>Últimos 7 días</option>
          <option value={30}>Últimos 30 días</option>
          <option value={90}>Últimos 90 días</option>
          <option value={365}>Último año</option>
        </select>
        {error && <div className="status status-error" role="alert"><p>{error}</p></div>}
        {!error && !data && <p role="status">Cargando indicadores…</p>}
        {data && data.total_requests === 0 && <div className="status"><p>No hay datos disponibles para este periodo.</p></div>}
        {data && data.total_requests > 0 && (
          <dl className="metrics-grid" aria-live="polite">
            <div><dt>Solicitudes registradas</dt><dd>{data.total_requests}</dd></div>
            <div><dt>Consultas atendidas</dt><dd>{data.queries_attended}</dd></div>
            <div><dt>Solicitudes con error</dt><dd>{data.requests_with_error}</dd></div>
            <div><dt>Tiempo medio</dt><dd>{data.average_response_ms} ms</dd></div>
            <div><dt>Tiempo máximo</dt><dd>{data.maximum_response_ms} ms</dd></div>
          </dl>
        )}
      </section>
    </AuthenticatedShell>
  );
}
