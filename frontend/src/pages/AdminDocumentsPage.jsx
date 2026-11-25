import { useCallback, useEffect, useState } from "react";
import {
  createAdminDocument,
  getAdminDocument,
  listAdminDocuments,
  setAdminDocumentStatus,
  updateAdminDocument,
} from "../api/client";
import AuthenticatedShell from "../components/AuthenticatedShell.jsx";

const blankForm = { title: "", topic: "", content: "" };

export default function AdminDocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [form, setForm] = useState(blankForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listAdminDocuments();
      setDocuments(response.data);
      setError("");
    } catch {
      setError("No se pudo cargar el catálogo. Verifica que el backend esté disponible.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  function changeField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function beginEdit(documentId) {
    setError("");
    setNotice("");
    try {
      const response = await getAdminDocument(documentId);
      setForm({
        title: response.data.title || "",
        topic: response.data.topic || "",
        content: response.data.content || "",
      });
      setEditingId(documentId);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError("No se pudo abrir el documento para editarlo.");
    }
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(blankForm);
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      if (editingId) {
        await updateAdminDocument(editingId, form);
        setNotice("Documento actualizado y enviado a reindexación.");
      } else {
        await createAdminDocument(form);
        setNotice("Documento incorporado e indexado.");
      }
      setForm(blankForm);
      setEditingId(null);
      await loadDocuments();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      setError(status === 409 && typeof detail === "string"
        ? detail
        : status === 400 || status === 422
          ? "Revisa el título, tema y contenido. El contenido debe tener hasta 20 000 caracteres."
          : "No se pudo guardar o indexar el documento. Revisa el estado del backend.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(item) {
    setError("");
    setNotice("");
    const nextStatus = item.status === "ACTIVO" ? "INACTIVO" : "ACTIVO";
    try {
      await setAdminDocumentStatus(item.id, nextStatus);
      setNotice(nextStatus === "ACTIVO" ? "Documento habilitado e indexado." : "Documento deshabilitado y retirado del índice.");
      await loadDocuments();
    } catch {
      setError("No se pudo cambiar el estado del documento.");
    }
  }

  return (
    <AuthenticatedShell>
      <section className="card card-wide">
        <p className="eyebrow">HU-13</p>
        <h1>Administración de documentos</h1>
        <p className="lead">Los documentos inactivos conservan su registro y dejan de participar en la recuperación de respuestas.</p>
        <form className="form" onSubmit={submit} aria-busy={saving}>
          <h2>{editingId ? "Actualizar documento" : "Incorporar documento"}</h2>
          <label htmlFor="doc-title">Título</label>
          <input id="doc-title" name="title" value={form.title} onChange={changeField}
            required maxLength={200} disabled={saving} />
          <label htmlFor="doc-topic">Tema</label>
          <input id="doc-topic" name="topic" value={form.topic} onChange={changeField}
            required maxLength={50} disabled={saving} />
          <label htmlFor="doc-content">Contenido agrícola</label>
          <textarea id="doc-content" name="content" value={form.content} onChange={changeField}
            required maxLength={20000} rows={8} disabled={saving}
            aria-describedby="doc-content-help" />
          <p id="doc-content-help" className="document-meta">Hasta 20 000 caracteres. Revisa el contenido antes de guardarlo.</p>
          <div className="form-actions">
            <button type="submit" disabled={saving}>{saving ? "Guardando e indexando…" : editingId ? "Guardar cambios" : "Registrar documento"}</button>
            {editingId && <button type="button" className="button-secondary" onClick={cancelEdit} disabled={saving}>Cancelar edición</button>}
          </div>
        </form>
        {error && <div className="status status-error" role="alert"><p>{error}</p></div>}
        {notice && <div className="status status-ok" role="status"><p>{notice}</p></div>}
        <h2 className="section-heading">Catálogo</h2>
        {loading ? <p role="status">Cargando documentos…</p> : documents.length === 0 ? <p>No hay documentos registrados.</p> : (
          <ul className="document-list">
            {documents.map((item) => (
              <li key={item.id}>
                <div className="document-row">
                  <div>
                    <strong>{item.title}</strong> · {item.topic}
                    <p className="document-meta">Estado: {item.status} · Versión: {item.version}</p>
                    <p className="document-meta">{item.source_path}</p>
                  </div>
                  <div className="form-actions">
                    <button type="button" className="button-secondary" onClick={() => beginEdit(item.id)}>Editar</button>
                    <button type="button" onClick={() => toggleStatus(item)} aria-label={(item.status === "ACTIVO" ? "Deshabilitar " : "Habilitar ") + item.title}>
                      {item.status === "ACTIVO" ? "Deshabilitar" : "Habilitar"}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </AuthenticatedShell>
  );
}
