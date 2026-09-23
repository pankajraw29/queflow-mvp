import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";

export default function QueueJoin() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState("");

  const load = useCallback(async () => {
    try {
      const d = await api.publicQueue(code);
      setInfo(d);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [code]);

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  const join = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setJoinError("");
    setJoining(true);
    try {
      const res = await api.joinQueue(code, name.trim());
      navigate(`/q/${code}/t/${res.ticket_id}`);
    } catch (err) {
      setJoinError(err.message);
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="container narrow center">
        <p className="muted">Loading queue…</p>
      </div>
    );
  }

  if (error || !info) {
    return (
      <div className="container narrow">
        <div className="card center">
          <div className="status-icon">🚫</div>
          <h1>{error || "Queue not found"}</h1>
          <p className="muted">
            This queue may be closed or the link may be incorrect. Please check
            with the staff.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container narrow">
      <div className="card">
        <p className="muted center">{info.business_name}</p>
        <h1 className="center">{info.queue_name}</h1>
        <p className="center big-stat">
          <strong>{info.waiting_count}</strong>{" "}
          {info.waiting_count === 1 ? "person" : "people"} waiting
        </p>
        {joinError && <div className="alert alert-error">{joinError}</div>}
        <form onSubmit={join}>
          <label className="field">
            <span>Your name</span>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name to join"
              autoComplete="name"
            />
          </label>
          <button className="btn btn-primary btn-block btn-lg" disabled={joining}>
            {joining ? "Joining…" : "Join queue"}
          </button>
        </form>
      </div>
    </div>
  );
}
