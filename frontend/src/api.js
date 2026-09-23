// QueueFlow API client. Base URL comes from VITE_API_URL (see .env.example).
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("qf_token");
}

export function getBusiness() {
  try {
    return JSON.parse(localStorage.getItem("qf_business"));
  } catch {
    return null;
  }
}

export function setAuth(token, business) {
  localStorage.setItem("qf_token", token);
  localStorage.setItem("qf_business", JSON.stringify(business));
}

export function clearAuth() {
  localStorage.removeItem("qf_token");
  localStorage.removeItem("qf_business");
}

async function req(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const t = getToken();
    if (t) headers.Authorization = `Bearer ${t}`;
  }
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    const err = new Error("Could not reach the server. Check your connection and try again.");
    err.status = 0;
    throw err;
  }
  if (res.status === 204) return null;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON response */
  }
  if (!res.ok) {
    const detail = data && (data.detail || data.message);
    const msg =
      typeof detail === "string"
        ? detail
        : `Request failed (HTTP ${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  health: () => req("/api/health"),

  register: (payload) =>
    req("/api/auth/register", { method: "POST", body: payload }),
  login: (payload) => req("/api/auth/login", { method: "POST", body: payload }),
  me: () => req("/api/auth/me", { auth: true }),

  listQueues: () => req("/api/queues", { auth: true }),
  createQueue: (name) =>
    req("/api/queues", { method: "POST", body: { name }, auth: true }),
  getQueue: (id) => req(`/api/queues/${id}`, { auth: true }),
  updateQueue: (id, patch) =>
    req(`/api/queues/${id}`, { method: "PATCH", body: patch, auth: true }),
  deleteQueue: (id) => req(`/api/queues/${id}`, { method: "DELETE", auth: true }),
  resetQueue: (id) =>
    req(`/api/queues/${id}/reset`, { method: "POST", auth: true }),
  callNext: (id) =>
    req(`/api/queues/${id}/call-next`, { method: "POST", auth: true }),
  completeCurrent: (id) =>
    req(`/api/queues/${id}/complete-current`, { method: "POST", auth: true }),
  skipCurrent: (id) =>
    req(`/api/queues/${id}/skip-current`, { method: "POST", auth: true }),

  publicQueue: (code) => req(`/api/pub/q/${code}`),
  joinQueue: (code, customer_name) =>
    req(`/api/pub/q/${code}/join`, {
      method: "POST",
      body: { customer_name },
    }),
  ticketStatus: (code, ticket_id) =>
    req(`/api/pub/q/${code}/t/${ticket_id}`),
};

export function joinUrl(code) {
  return `${window.location.origin}/q/${code}`;
}
