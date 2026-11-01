import assert from "node:assert/strict";
import { test } from "node:test";
import { destinoHealth, mensajeErrorConexion } from "./conexion.js";

const DESTINO = "https://agro-asistente-api.onrender.com/health";

test("el destino de health no duplica la ruta", () => {
  assert.equal(destinoHealth("https://agro-asistente-api.onrender.com"), DESTINO);
  assert.equal(destinoHealth(""), "/health");
});

test("un tiempo agotado no se presenta como fallo genérico", () => {
  const texto = mensajeErrorConexion({ code: "ECONNABORTED" }, DESTINO);
  assert.match(texto, /no respondió a tiempo/);
  assert.match(texto, /agro-asistente-api\.onrender\.com\/health/);
  assert.doesNotMatch(texto, /\/health\/health/);
});

test("una respuesta HTTP conserva el código y el detalle", () => {
  const texto = mensajeErrorConexion(
    { response: { status: 503, data: { detail: "mysql disconnected" } } },
    DESTINO,
  );
  assert.match(texto, /HTTP 503/);
  assert.match(texto, /mysql disconnected/);
});

test("un bloqueo del cliente se distingue de un error HTTP", () => {
  const texto = mensajeErrorConexion({ code: "ERR_NETWORK", message: "Network Error" }, DESTINO);
  assert.match(texto, /ERR_BLOCKED_BY_CLIENT/);
  assert.match(texto, /bloqueador del cliente/);
  assert.doesNotMatch(texto, /HTTP /);
});
