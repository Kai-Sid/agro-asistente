import { useState } from "react";
import { Link } from "react-router-dom";
import { registerAdmin } from "../api/client";
import PublicShell from "../components/PublicShell.jsx";
import {
  aplicarMensajeValidacion,
  limpiarMensajeValidacion,
} from "../forms/validacionEsp.js";

export default function AdminRegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmation) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      const response = await registerAdmin({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
      });
      setSuccess("Administrador creado para " + response.data.email + ". Ya puedes iniciar sesión.");
      setName("");
      setEmail("");
      setPassword("");
      setConfirmation("");
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 409) {
        setError(
          typeof detail === "string"
            ? detail
            : "El registro inicial ya está cerrado o el correo ya existe.",
        );
      } else if (status === 422 || status === 400) {
        setError(
          typeof detail === "string"
            ? detail
            : "Revisa los datos. La contraseña debe tener al menos 12 caracteres.",
        );
      } else {
        setError(
          "No se pudo completar el registro. Verifica la conexión e inténtalo de nuevo.",
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <PublicShell>
      <section className="card">
        <p className="eyebrow">Configuración inicial</p>
        <h1>Registrar administrador</h1>
        <p className="lead">
          Este formulario permite registrar el primer administrador del sistema.
          Después de crearlo, el registro público se cierra.
        </p>

        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="admin-register-name">Nombre</label>
          <input
            id="admin-register-name"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            onInvalid={aplicarMensajeValidacion}
            onInput={limpiarMensajeValidacion}
            autoComplete="name"
            maxLength={120}
            required
            disabled={loading || Boolean(success)}
          />

          <label htmlFor="admin-register-email">Correo</label>
          <input
            id="admin-register-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            onInvalid={aplicarMensajeValidacion}
            onInput={limpiarMensajeValidacion}
            autoComplete="email"
            maxLength={150}
            required
            disabled={loading || Boolean(success)}
          />

          <label htmlFor="admin-register-password">Contraseña</label>
          <input
            id="admin-register-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onInvalid={aplicarMensajeValidacion}
            onInput={limpiarMensajeValidacion}
            autoComplete="new-password"
            minLength={12}
            maxLength={72}
            required
            disabled={loading || Boolean(success)}
          />

          <label htmlFor="admin-register-confirmation">Confirmar contraseña</label>
          <input
            id="admin-register-confirmation"
            type="password"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            onInvalid={aplicarMensajeValidacion}
            onInput={limpiarMensajeValidacion}
            autoComplete="new-password"
            minLength={12}
            maxLength={72}
            required
            disabled={loading || Boolean(success)}
          />

          <button type="submit" disabled={loading || Boolean(success)}>
            {loading ? "Registrando…" : "Registrar administrador"}
          </button>
        </form>

        {success && (
          <div className="status status-ok" role="status">
            <p>{success}</p>
          </div>
        )}
        {error && (
          <div className="status status-error" role="alert">
            <p>{error}</p>
          </div>
        )}

        <p className="nav-link">
          <Link to="/admin/login">Ir al inicio de sesión administrativo</Link>
          {" · "}
          <Link to="/">Volver al inicio</Link>
        </p>
      </section>
    </PublicShell>
  );
}
