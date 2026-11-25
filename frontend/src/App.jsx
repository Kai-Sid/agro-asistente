import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import AdminLoginPage from "./pages/AdminLoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import ContextPage from "./pages/ContextPage.jsx";
import QueryPage from "./pages/QueryPage.jsx";
import RiskPage from "./pages/RiskPage.jsx";
import AdminDashboardPage from "./pages/AdminDashboardPage.jsx";
import AdminDocumentsPage from "./pages/AdminDocumentsPage.jsx";
import AdminMetricsPage from "./pages/AdminMetricsPage.jsx";
import AdminEvaluationsPage from "./pages/AdminEvaluationsPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route element={<ProtectedRoute role="AGRICULTOR" />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/context" element={<ContextPage />} />
        <Route path="/query" element={<QueryPage />} />
        <Route path="/riesgo" element={<RiskPage />} />
      </Route>
      <Route element={<ProtectedRoute role="ADMINISTRADOR" />}>
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/admin/documents" element={<AdminDocumentsPage />} />
        <Route path="/admin/metrics" element={<AdminMetricsPage />} />
        <Route path="/admin/evaluations" element={<AdminEvaluationsPage />} />
      </Route>
    </Routes>
  );
}
