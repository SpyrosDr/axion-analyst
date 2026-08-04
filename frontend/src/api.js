const BASE = "/api";
const TOKEN_KEY = "aletheia_token";

let authToken = null;
let onUnauthorized = null;

export function setAuthToken(token) {
  authToken = token;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function loadStoredToken() {
  authToken = localStorage.getItem(TOKEN_KEY);
  return authToken;
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

async function errorDetail(res) {
  let detail;
  try {
    detail = (await res.json()).detail;
  } catch {
    return null;
  }
  if (Array.isArray(detail)) {
    // FastAPI validation errors (422) arrive as a list of error objects.
    return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  }
  return detail;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    setAuthToken(null);
    if (onUnauthorized) onUnauthorized();
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const detail = await errorDetail(res);
    throw new Error(detail || `Request failed: ${res.status} ${res.statusText}`);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export async function login(username, password) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${BASE}/auth/login`, { method: "POST", body });
  if (!res.ok) {
    const detail = await errorDetail(res);
    throw new Error(detail || "Login failed");
  }
  return res.json();
}

export function getMe() {
  return request("/auth/me");
}

export function createUser({ username, password, is_admin = false }) {
  return request("/auth/users", {
    method: "POST",
    body: JSON.stringify({ username, password, is_admin }),
  });
}

export function listUsers() {
  return request("/auth/users");
}

export function listUsersDetailed() {
  return request("/auth/users/detailed");
}

export function updateUserRole(userId, globalRole) {
  return request(`/auth/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ global_role: globalRole }),
  });
}

export function changePassword(currentPassword, newPassword) {
  return request("/auth/me/password", {
    method: "PUT",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export function updateProfile({ username, display_name, avatar_url, avatar_color }) {
  return request("/auth/me", {
    method: "PUT",
    body: JSON.stringify({ username, display_name, avatar_url, avatar_color }),
  });
}

export function addCollaborator(caseId, username, role) {
  return request(`/cases/${caseId}/collaborators`, {
    method: "POST",
    body: JSON.stringify({ username, role }),
  });
}

export function listCollaborators(caseId) {
  return request(`/cases/${caseId}/collaborators`);
}

export function updateCollaboratorRole(caseId, userId, role) {
  return request(`/cases/${caseId}/collaborators/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function removeCollaborator(caseId, userId) {
  return request(`/cases/${caseId}/collaborators/${userId}`, {
    method: "DELETE",
  });
}

export function createCase({ context, description, evidence_items }) {
  return request("/cases", {
    method: "POST",
    body: JSON.stringify({ context, description, evidence_items }),
  });
}

export function listCases() {
  return request("/cases");
}

export function getCase(caseId) {
  return request(`/cases/${caseId}`);
}

export function deleteCase(caseId) {
  return request(`/cases/${caseId}`, { method: "DELETE" });
}

export function updateCaseStatus(caseId, status) {
  return request(`/cases/${caseId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function listActivity(caseId) {
  return request(`/cases/${caseId}/activity`);
}

export function addEvidence(caseId, { title, type, content }) {
  return request(`/cases/${caseId}/evidence`, {
    method: "POST",
    body: JSON.stringify({ title, type, content }),
  });
}

export function runAnalysis(caseId) {
  return request(`/cases/${caseId}/report`, { method: "POST" });
}

export function runEntitySearch({ query, entity_type, case_id }) {
  return request("/tools/entity-search", {
    method: "POST",
    body: JSON.stringify({ query, entity_type, case_id }),
  });
}

export function listEntitySearches({ case_id } = {}) {
  return request(`/tools/entity-search${case_id ? `?case_id=${case_id}` : ""}`);
}

export function getEntitySearch(id) {
  return request(`/tools/entity-search/${id}`);
}
