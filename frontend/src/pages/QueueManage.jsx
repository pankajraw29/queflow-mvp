import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import QRCode from "react-qr-code";
import { api, joinUrl } from "../api.js";

export default function QueueManage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null); // { queue, tickets }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const qrWrapRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const d = await api.getQueue(id);
      setData(d);
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
  }, [id, navigate]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  const runAction = async (fn, confirmMsg) => {
    if (!window.confirm(confirmMsg)) return;
    setActionError("");
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const toggleOpen = () =>
    runAction(
      () => api.updateQueue(id, { is_open: !queue.is_open }),
      queue.is_open
        ? `Close the queue "${queue.name}"? Customers will no longer be able to join.`
        : `Open the queue "${queue.name}"? Customers will be able to join again.`
    );

  const copyLink = async () => {
    const url = joinUrl(queue.code);
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Fallback for browsers without clipboard permission
      const ta = document.createElement("textarea");
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadQR = () => {
    const svg = qrWrapRef.current?.querySelector("svg");
    if (!svg) return;
    const blob = new Blob([new XMLSerializer().serializeToString(svg)], {
      type: "image/svg+xml",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `queueflow-${queue.code}-qr.svg`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="container">
        <p className="muted">Loading queue…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container narrow">
        <div className="alert alert-error">{error}</div>
        <Link to="/dashboard" className="btn btn-outline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const { queue, tickets } = data;
  const serving = tickets.find((t) => t.status === "serving");
  const waiting = tickets.filter((t) => t.status === "waiting");

  return (
    <div className="container">
      <Link to="/dashboard" className="back-link">
        ← Back to dashboard
      </Link>
      <div className="page-head">
        <div>
          <h1>{queue.name}</h1>
          <p className="muted">
            Code <code>{queue.code}</code>
            <span className="dot">·</span>
            <span className={`badge ${queue.is_open ? "badge-open" : "badge-closed"}`}>
              {queue.is_open ? "Open" : "Closed"}
            </span>
          </p>
        </div>
        <button className="btn btn-outline" onClick={toggleOpen} disabled={busy}>
          {queue.is_open ? "Close queue" : "Open queue"}
        </button>
      </div>

      {actionError && <div className="alert alert-error">{actionError}</div>}

      <div className="manage-grid">
        <div className="card">
          <h2 className="card-title">Customer join link</h2>
          <div className="qr-wrap" ref={qrWrapRef}>
            <QRCode value={joinUrl(queue.code)} size={220} />
          </div>
          <p className="join-url">{joinUrl(queue.code)}</p>
          <div className="row">
            <button className="btn btn-outline btn-sm" onClick={copyLink}>
              {copied ? "Copied!" : "Copy link"}
            </button>
            <button className="btn btn-outline btn-sm" onClick={downloadQR}>
              Download QR
            </button>
          </div>
          <p className="muted small">
            Print the QR code and place it at your counter. Customers scan it to join.
          </p>
        </div>

        <div className="card">
          <h2 className="card-title">Queue controls</h2>
          {serving ? (
            <div className="serving-banner">
              <span className="muted">Now serving</span>
              <span className="serving-number">{serving.number}</span>
              <span className="muted">{serving.customer_name}</span>
            </div>
          ) : (
            <p className="muted">Nobody is being served right now.</p>
          )}
          <div className="controls">
            <button
              className="btn btn-primary"
              disabled={busy}
              onClick={() =>
                runAction(
                  () => api.callNext(id),
                  "Call the next ticket in line?"
                )
              }
            >
              Call Next
            </button>
            <button
              className="btn btn-success"
              disabled={busy || !serving}
              onClick={() =>
                runAction(
                  () => api.completeCurrent(id),
                  `Mark ticket ${serving?.number} as completed?`
                )
              }
            >
              Complete Current
            </button>
            <button
              className="btn btn-outline"
              disabled={busy || !serving}
              onClick={() =>
                runAction(
                  () => api.skipCurrent(id),
                  `Skip ticket ${serving?.number}? The customer will be marked as skipped.`
                )
              }
            >
              Skip Current
            </button>
            <button
              className="btn btn-danger-ghost"
              disabled={busy}
              onClick={() =>
                runAction(
                  () => api.resetQueue(id),
                  "Reset this queue? ALL tickets will be cleared and numbering restarts. This cannot be undone."
                )
              }
            >
              Reset queue
            </button>
          </div>
        </div>
      </div>

      <h2 className="section-title">
        Live tickets <span className="muted small">· refreshes every 5s</span>
      </h2>
      {tickets.length === 0 ? (
        <div className="card empty-state">
          <p className="muted">No active tickets. Share the QR code to let customers join.</p>
        </div>
      ) : (
        <div className="card ticket-list">
          {tickets.map((t) => (
            <div
              key={t.id}
              className={`ticket-row ${t.status === "serving" ? "ticket-serving" : ""}`}
            >
              <span className="ticket-num">{t.number}</span>
              <span className="ticket-name">{t.customer_name}</span>
              <span className={`badge badge-${t.status}`}>{t.status}</span>
            </div>
          ))}
          {waiting.length > 0 && (
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              {waiting.length} waiting
            </p>
          )}
        </div>
      )}
    </div>
  );
}
