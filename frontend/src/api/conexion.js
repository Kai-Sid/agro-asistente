export function destinoHealth(viteEnv) {
  const base = typeof viteEnv === "string" ? viteEnv : "";
  return base ? `${base}/health` : "/health";
}

export function mensajeErrorConexion(error, destino) {
  const sitio = destino || "/health";
  if (error?.code === "ECONNABORTED") {
    return `El backend no respondió a tiempo al consultar ${sitio}.`;
  }
  const status = error?.response?.status;
  if (typeof status === "number") {
    const detail = error.response?.data?.detail;
    const motivo = typeof detail === "string" && detail.trim() ? `: ${detail.trim()}` : "";
    return `El backend respondió HTTP ${status} al consultar ${sitio}${motivo}.`;
  }
  return (
    `El navegador no completó la solicitud a ${sitio}. ` +
    "Si la consola muestra net::ERR_BLOCKED_BY_CLIENT, un bloqueador del cliente impidió la conexión."
  );
}
