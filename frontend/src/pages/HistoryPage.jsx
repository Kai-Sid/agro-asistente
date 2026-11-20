import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAgriculturalQueries } from "../api/client";
import AuthFooter from "../components/AuthFooter.jsx";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    listAgriculturalQueries(20)
      .then((response) => {
        setItems(Array.isArray(response.data) ? response.data : []);
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          return;
        }
        setError("No se pudo cargar el historial de consultas.");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">Historial</p>
        <h1>Consultas anteriores</h1>
        <p className="lead">
          Revisa las consultas que ya registraste. Para una nueva consulta ve a{" "}
          <Link to="/query">Consulta agrícola</Link>.
        </p>

        {loading && <p>Cargando historial…</p>}
        {error && (
          <div className="status status-error" role="alert">
            <p>{error}</p>
          </div>
        )}
        {!loading && !error && items.length === 0 && (
          <p>Aún no hay consultas registradas para tu cuenta.</p>
        )}

        <ul className="document-list">
          {items.map((item) => (
            <li key={item.id}>
              <div>
                <strong>{item.text}</strong>
              </div>
              <p className="document-meta">
                {item.created_at || "sin fecha"}
                {item.generation_method ? ` · ${item.generation_method}` : ""}
              </p>
              {item.answer ? (
                <p>{item.answer.length > 280 ? `${item.answer.slice(0, 280)}…` : item.answer}</p>
              ) : (
                <p className="document-meta">Sin respuesta persistida.</p>
              )}
            </li>
          ))}
        </ul>

        <AuthFooter />
      </section>
    </AuthenticatedShell>
  );
}
