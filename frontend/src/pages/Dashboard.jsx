import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getBusiness } from "../api.js";

export default function Dashboard() {
  const [queues, setQueues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const biz = getBusiness();

  const load = useCallback(async () => {
    try {
      const qs = await api.listQueues();
      setQueues(qs);
      setError("");
    } catch (err) {
      if (err.status === 401) {
        navigate("/login");
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    load();
  }, [load]);

  const createQueue = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setError("");
    setCreating(true);
    try {
      await api.createQueue(newName.trim());
      setNewName("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const toggleOpen = async (q) => {
    setError("");
    try {
      await api.updateQueue(q.id, { is_open: !q.is_open });
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteQueue = async (q) => {
    if (
      !window.confirm(
        `Delete the queue "${q.name}"? This removes the queue and all its tickets permanently.`
      )
    ) {
      return;
    }
    setError("");
    try {
      await api.deleteQueue(q.id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">
            {biz?.business_name ? `Managing queues for ${biz.business_name}` : "Your queues"}
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2 className="card-title">Create a new queue</h2>
        <form onSubmit={createQueue} className="inline-form">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="e.g. General Consultation"
            aria-label="Queue name"
          />
          <button className="btn btn-primary" disabled={creating || !newName.trim()}>
            {creating ? "Creating…" : "Create queue"}
          </button>
        </form>
      </div>

      <h2 className="section-title">Your queues</h2>
      {loading ? (
        <p className="muted">Loading queues…</p>
      ) : queues.length === 0 ? (
        <div className="card empty-state">
          <p className="muted">
            No queues yet. Create your first queue above to get its QR code and join link.
          </p>
        </div>
      ) : (
        <div className="queue-grid">
          {queues.map((q) => (
            <div key={q.id} className="card queue-card">
              <div className="queue-card-top">
                <h3>{q.name}</h3>
                <span className={`badge ${q.is_open ? "badge-open" : "badge-closed"}`}>
                  {q.is_open ? "Open" : "Closed"}
                </span>
              </div>
              <p className="queue-meta">
                <strong>{q.waiting_count}</strong> waiting
                <span className="dot">·</span> Code <code>{q.code}</code>
              </p>
              <div className="queue-actions">
                <Link to={`/queues/${q.id}`} className="btn btn-primary btn-sm">
                  Manage
                </Link>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => toggleOpen(q)}
                >
                  {q.is_open ? "Close" : "Open"}
                </button>
                <button
                  className="btn btn-danger-ghost btn-sm"
                  onClick={() => deleteQueue(q)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
