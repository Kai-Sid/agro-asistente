import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginAdmin, saveAccessToken, saveSessionAdmin } from "../api/client";
import PublicShell from "../components/PublicShell.jsx";

export default function AdminLoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await loginAdmin({ email: email.trim(), password });
      saveAccessToken(response.data.access_token);
      saveSessionAdmin(response.data);
      setPassword("");
      navigate("/admin", { replace: true });
    } catch (err) {
      const status = err.response?.status;
      setError(status === 401 ? "Correo o contraseña incorrectos." : "No se pudo iniciar sesión. Revisa la conexión e inténtalo nuevamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PublicShell>
      <section className="card">
        <p className="eyebrow">Acceso administrativo</p>
        <h1>Agro-Asistente</h1>
        <p className="lead">Ingresa con una cuenta de administrador autorizada.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="admin-email">Correo</label>
          <input id="admin-email" type="email" autoComplete="username" required maxLength={150}
            value={email} onChange={(event) => setEmail(event.target.value)} disabled={loading} />
          <label htmlFor="admin-password">Contraseña</label>
          <input id="admin-password" type="password" autoComplete="current-password" required
            value={password} onChange={(event) => setPassword(event.target.value)} disabled={loading} />
          <button type="submit" disabled={loading}>{loading ? "Ingresando…" : "Ingresar como administrador"}</button>
        </form>
        {error && <div className="status status-error" role="alert"><p>{error}</p></div>}
      </section>
    </PublicShell>
  );
}
