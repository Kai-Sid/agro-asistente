import axios from "axios";
import { urlBaseApi } from "./baseUrl.js";

export const api = axios.create({
  baseURL: urlBaseApi(import.meta.env),
  timeout: 5000,
});

const ACCESS_TOKEN_KEY = "agro_asistente_access_token";
const PUBLIC_AUTH_PATHS = ["/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/admin/auth/login"];\nconst SESSION_ROLE_KEY = "agro_asistente_session_role";

export function saveAccessToken(token) {
  if (typeof token !== "string" || !token.trim()) {
    return;
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token.trim());
}

export function getAccessToken() {
  const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  if (!token || token === "undefined" || token === "null") {
    return null;
  }
  return token;
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

const SESSION_FARMER_KEY = "agro_asistente_session_farmer";

export function saveSessionFarmer(farmer) {
  const names = typeof farmer?.names === "string" ? farmer.names.trim() : "";
  const lastNames = typeof farmer?.last_names === "string" ? farmer.last_names.trim() : "";
  const email = typeof farmer?.email === "string" ? farmer.email.trim() : "";
  const displayName = [names, lastNames].filter(Boolean).join(" ") || email;
  if (!displayName) {
    return;
  }
  window.localStorage.setItem(SESSION_FARMER_KEY, displayName);\n  window.localStorage.setItem(SESSION_ROLE_KEY, "AGRICULTOR");
}

export function getSessionFarmer() {
  return window.localStorage.getItem(SESSION_FARMER_KEY);
}

export function clearSession() {
  clearAccessToken();
  window.localStorage.removeItem(SESSION_FARMER_KEY);\n  window.localStorage.removeItem(SESSION_ROLE_KEY);
}

function isPublicAuthRequest(config) {
  const url = `${config.baseURL || ""}${config.url || ""}`;
  return PUBLIC_AUTH_PATHS.some((path) => url.includes(path));
}

api.interceptors.request.use((config) => {
  if (isPublicAuthRequest(config)) {
    return config;
  }
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !isPublicAuthRequest(error.config || {})) {
      clearSession();
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

export function getHealth() {
  return api.get("/health", { timeout: 60000 });
}

export function registerFarmer(payload) {
  return api.post("/api/v1/auth/register", payload);
}

export function loginFarmer(payload) {
  return api.post("/api/v1/auth/login", payload);
}

export function listContexts() {
  return api.get("/api/v1/contexts");
}

export function createAgriculturalContext(payload) {
  return api.post("/api/v1/contexts", payload);
}

export function selectContext(contextId) {
  return api.post(`/api/v1/contexts/${contextId}/select`);
}

export function submitAgriculturalQuery(payload) {
  return api.post("/api/v1/queries", payload, { timeout: 120000 });
}

export function predictAgriculturalRisk(payload) {
  return api.post("/api/v1/riesgo", payload, { timeout: 120000 });
}

export function listKnowledgeDocuments() {
  return api.get("/api/v1/knowledge/documents");
}

export function ingestKnowledge(payload) {
  return api.post("/api/v1/knowledge/ingest", payload);
}
\nexport function loginAdmin(payload) {\n  return api.post("/api/v1/admin/auth/login", payload);\n}\n\nexport function listAdminDocuments() {\n  return api.get("/api/v1/admin/documents");\n}\n\nexport function createAdminDocument(payload) {\n  return api.post("/api/v1/admin/documents", payload);\n}\n\nexport function getAdminDocument(documentId) {\n  return api.get(`/api/v1/admin/documents/${documentId}`);\n}\n\nexport function updateAdminDocument(documentId, payload) {\n  return api.put(`/api/v1/admin/documents/${documentId}`, payload);\n}\n\nexport function setAdminDocumentStatus(documentId, status) {\n  return api.patch(`/api/v1/admin/documents/${documentId}/status`, { status });\n}\n\nexport function getAdminMetrics(days = 30) {\n  return api.get("/api/v1/admin/metrics", { params: { days } });\n}\n