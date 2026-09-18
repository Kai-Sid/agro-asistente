import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listContexts, submitAgriculturalQuery } from "../api/client";
import AuthFooter from "../components/AuthFooter.jsx";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

export default function QueryPage() {
  const [text, setText] = useState("");
  const [selectedContext, setSelectedContext] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [error, setError] = useState("");

  function loadSelectedContext() {
    setLoadingContext(true);
    listContexts()
      .then((response) => {
        const current = response.data.find((item) => item.is_selected) || null;
        setSelectedContext(current);
      })
      .catch(() => {})
      .finally(() => setLoadingContext(false));
  }

  useEffect(() => {
    loadSelectedContext();
  }, []);

  function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    submitAgriculturalQuery({ text })
      .then((response) => {
        setResult(response.data);
        setText("");
      })
      .catch((err) => {
        const status = err.response?.status;
        const detail = err.response?.data?.detail;
        if (status === 401) {
          return;
        }
        if (status === 409) {
          setError(typeof detail === "string" ? detail : "Debes seleccionar un contexto agrícola antes de consultar.");
        } else if (status === 400 || status === 422) {
          setError("Revisa el texto de la consulta. No puede estar vacío ni ser demasiado largo.");
        } else {
          setError("No se pudo enviar la consulta.");
        }
      })
      .finally(() => setLoading(false));
  }

  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">HU-04 / HU-06</p>
        <h1>Consulta agrícola</h1>
        <p className="lead">
          Escribe tu consulta en lenguaje natural. El sistema recupera fragmentos de la
          base de conocimiento (RAG básico) y construye una respuesta inicial por plantilla.
          Todavía no se usa un modelo de IA externo.
        </p>

        <section className="context-banner">
          <h2>Contexto actual</h2>
          {loadingContext && <p>Cargando contexto seleccionado…</p>}
          {!loadingContext && selectedContext && (
            <p>
              <strong>{selectedContext.crop}</strong> · {selectedContext.region}
              {selectedContext.plot_name ? ` · ${selectedContext.plot_name}` : ""}
            </p>
          )}
          {!loadingContext && !selectedContext && (
            <p>
              No hay un contexto agrícola seleccionado.{" "}
              <Link to="/context">Crear o seleccionar contexto</Link>
            </p>
          )}
        </section>

        <section className="query-box">
          <h2>¿Qué deseas consultar?</h2>
          <form className="form" onSubmit={handleSubmit}>
            <label>
              Consulta
              <textarea
                name="text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                required
                maxLength={2000}
                placeholder="¿Qué puedo hacer para mejorar el cultivo de papa?"
              />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? "Consultando…" : "Consultar"}
            </button>
          </form>
        </section>

        {error && <div className="status status-error"><p>{error}</p></div>}

        {result && (
          <>
            <section className="answer-panel">
              <h2>Respuesta</h2>
              <p className="lead">{result.answer}</p>
              <dl>
                <dt>Consulta</dt>
                <dd>{result.text}</dd>
                <dt>Contexto</dt>
                <dd>
                  {result.context.crop} · {result.context.region}
                  {result.context.plot_name ? ` · ${result.context.plot_name}` : ""}
                </dd>
                <dt>Método</dt>
                <dd>
                  {result.generation_method === "template"
                    ? "Plantilla RAG (PMV1)"
                    : result.generation_method}
                </dd>
                <dt>Fecha</dt>
                <dd>{result.created_at}</dd>
              </dl>
            </section>

            <section className="evidence-panel">
              <h2>Evidencias</h2>
              {(!result.evidences || result.evidences.length === 0) && (
                <p className="lead">
                  No se recuperó evidencia. No se encontró información suficiente en la
                  base de conocimiento.
                </p>
              )}
              {result.evidences && result.evidences.length > 0 && (
                <ul className="context-list">
                  {result.evidences.map((item) => (
                    <li key={`${item.chunk_id}-${item.rank_order}`}>
                      <div>
                        <strong>{item.document_title || "Documento agrícola"}</strong>
                      </div>
                      <p>{item.excerpt}</p>
                      <p className="document-meta">
                        Relevancia: {Number(item.similarity_score).toFixed(3)}
                        {" · "}
                        Documento: {item.document_id}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}

        <AuthFooter />
      </section>
    </AuthenticatedShell>
  );
}
