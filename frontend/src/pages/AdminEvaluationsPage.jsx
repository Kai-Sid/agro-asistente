import { useEffect, useState } from "react";
import { getAdminEvaluationDetails, listAdminEvaluations } from "../api/client";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

function score(value) {
  return value == null ? "—" : Number(value).toFixed(3);
}

export default function AdminEvaluationsPage() {
  const [evaluations, setEvaluations] = useState([]);
  const [details, setDetails] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    listAdminEvaluations()
      .then((response) => setEvaluations(response.data))
      .catch(() => setError("No se pudo cargar el historial de evaluaciones."))
      .finally(() => setLoading(false));
  }, []);

  async function showDetails(id) {
    setSelectedId(id);
    setDetailsLoading(true);
    setDetails([]);
    setError("");
    try {
      const response = await getAdminEvaluationDetails(id);
      setDetails(response.data);
    } catch {
      setError("No se pudieron cargar las muestras de esta evaluación.");
    } finally {
      setDetailsLoading(false);
    }
  }

  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">HU-16</p>
        <h1>Evaluación de inteligencia artificial</h1>
        <p className="lead">Cada corrida conserva dataset, proveedor, modelo, métricas y latencia para comparar resultados.</p>
        <p className="document-meta">La precisión y pertinencia léxicas son proxies automáticos; las métricas RAGAS requieren una corrida real con Ollama y juicio experto para conclusiones agronómicas.</p>
        {error && <div className="status status-error" role="alert"><p>{error}</p></div>}
        {loading && <p role="status">Cargando evaluaciones…</p>}
        {!loading && evaluations.length === 0 && <p>No hay corridas registradas. Ejecuta <code>python -m evaluation.run_baseline</code> desde la carpeta <code>backend</code>.</p>}
        {evaluations.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th><th>Dataset</th><th>Modelo</th><th>Precisión</th>
                  <th>Pertinencia</th><th>Fidelidad</th><th>Recall contexto</th><th>Tiempo medio</th><th>Muestras</th><th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {evaluations.map((item) => (
                  <tr key={item.id}>
                    <td>{item.created_at}</td><td>{item.dataset_version}</td>
                    <td>{item.provider} · {item.model}</td>
                    <td>{score(item.retrieval_precision)}</td><td>{score(item.answer_pertinence)}</td>
                    <td>{score(item.faithfulness)}</td><td>{score(item.context_recall)}</td>
                    <td>{score(item.average_response_ms)} ms</td><td>{item.sample_count}</td>
                    <td><button type="button" className="button-secondary" onClick={() => showDetails(item.id)}>Ver muestras</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {detailsLoading && <p role="status">Cargando muestras…</p>}
        {selectedId && !detailsLoading && details.length > 0 && (
          <section className="evaluation-details" aria-live="polite">
            <h2>Evaluación {selectedId}</h2>
            {details.map((item) => (
              <article className="evaluation-sample" key={item.item_id}>
                <h3>{item.item_id}</h3>
                <p><strong>Pregunta:</strong> {item.pregunta}</p>
                <p><strong>Precisión léxica:</strong> {score(item.precision_score)} · <strong>Pertinencia léxica:</strong> {score(item.pertinencia)} · <strong>Tiempo:</strong> {score(item.duracion_ms)} ms</p>
                <p><strong>Respuesta:</strong> {item.respuesta}</p>
              </article>
            ))}
          </section>
        )}
      </section>
    </AuthenticatedShell>
  );
}
