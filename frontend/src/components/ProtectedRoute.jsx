import { Navigate, Outlet } from "react-router-dom";
import { getAccessToken, getSessionRole } from "../api/client";

export default function ProtectedRoute({ role = "AGRICULTOR" }) {
  if (!getAccessToken()) {
    return <Navigate to={role === "ADMINISTRADOR" ? "/admin/login" : "/login"} replace />;
  }
  if (getSessionRole() !== role) {
    return <Navigate to={role === "ADMINISTRADOR" ? "/dashboard" : "/admin"} replace />;
  }
  return <Outlet />;
}
