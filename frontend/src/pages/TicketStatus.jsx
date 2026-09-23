import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";

export default function TicketStatus() {
  const { code, ticket_id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const t = await api.ticketStatus(code, ticket_id);
      setTicket(t);
      setError("");
    } catch (err) {
      if (err.status === 404) {
        setError("notfound");
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [code, ticket_id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [load]);

  if (loading) {
    return (
      <div className="container narrow center">
        <p className="muted">Checking your ticket…</p>
      </div>
    );
  }

  if (error === "notfound") {
    return (
      <div className="container narrow">
        <div className="card center">
          <div className="status-icon">🎫</div>
          <h1>Ticket not found</h1>
          <p className="muted">
            This ticket link is invalid or has expired. Please rejoin the queue
            or ask the staff for help.
          </p>
          <Link to={`/q/${code}`} className="btn btn-primary">
            Back to queue
          </Link>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container narrow">
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-outline" onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  const { number, status, ahead_count, queue_name } = ticket;

  return (
    <div className="container narrow">
      <div className={`card ticket-card status-${status}`}>
        <p className="muted center">{queue_name}</p>
        <p className="muted center small">Your ticket</p>
        <div className="big-ticket">{number}</div>

        {status === "waiting" && (
          <>
            <p className="center big-stat">
              <strong>{ahead_count}</strong>{" "}
              {ahead_count === 1 ? "person" : "people"} ahead of you
            </p>
            <p className="muted center small">
              Stay nearby — this page updates automatically.
            </p>
          </>
        )}

        {status === "serving" && (
          <div className="turn-banner">
            <div className="turn-emoji">🎉</div>
            <h2>It’s your turn!</h2>
            <p>Please proceed to the counter now.</p>
          </div>
        )}

        {status === "done" && (
          <div className="center">
            <div className="status-icon">✅</div>
            <h2>Completed — thank you!</h2>
            <p className="muted">Your turn is over. Have a great day!</p>
          </div>
        )}

        {status === "skipped" && (
          <div className="center">
            <div className="status-icon">⏭️</div>
            <h2>You were skipped</h2>
            <p className="muted">
              Please rejoin the queue or ask the staff for help.
            </p>
            <Link to={`/q/${code}`} className="btn btn-primary">
              Rejoin queue
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
