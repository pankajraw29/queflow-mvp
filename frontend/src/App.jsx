import { Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import QueueManage from "./pages/QueueManage.jsx";
import QueueJoin from "./pages/QueueJoin.jsx";
import TicketStatus from "./pages/TicketStatus.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import { clearAuth, getToken, getBusiness } from "./api.js";

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  // Re-read auth on every navigation so login/logout reflect immediately.
  void location.pathname;
  const authed = !!getToken();
  const biz = getBusiness();

  const logout = () => {
    clearAuth();
    navigate("/");
  };

  return (
    <header className="site-header">
      <Link to="/" className="brand">
        <span className="brand-mark">Q</span> QueueFlow
      </Link>
      <nav className="site-nav">
        {authed ? (
          <>
            <span className="nav-user">{biz?.business_name || biz?.name}</span>
            <Link to="/dashboard" className="nav-link">
              Dashboard
            </Link>
            <button className="btn btn-ghost btn-sm" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">
              Log in
            </Link>
            <Link to="/register" className="btn btn-primary btn-sm">
              Get started
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <div className="app">
      <Header />
      <main className="main">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/queues/:id"
            element={
              <ProtectedRoute>
                <QueueManage />
              </ProtectedRoute>
            }
          />
          <Route path="/q/:code" element={<QueueJoin />} />
          <Route path="/q/:code/t/:ticket_id" element={<TicketStatus />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <p>QueueFlow — smart queues for modern businesses.</p>
      </footer>
    </div>
  );
}

function NotFound() {
  return (
    <div className="container narrow center">
      <h1>Page not found</h1>
      <p className="muted">The page you are looking for does not exist.</p>
      <Link to="/" className="btn btn-primary">
        Back to home
      </Link>
    </div>
  );
}
