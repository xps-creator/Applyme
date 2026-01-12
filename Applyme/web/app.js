const API = "http://localhost:8000";

const el = (id) => document.getElementById(id);

function setAuthStatus(t) { el("authStatus").textContent = t; }
function setBatchStatus(t) { el("batchStatus").textContent = t; }

function getToken() { return localStorage.getItem("applyme_token") || ""; }
function setToken(t) { localStorage.setItem("applyme_token", t); }
function clearToken() { localStorage.removeItem("applyme_token"); }

function renderApps(apps) {
  const tbody = el("appsTbody");
  tbody.innerHTML = "";
  if (!apps || apps.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="3" class="small">Aucune donnée (fais tourner n8n puis refresh)</td>`;
    tbody.appendChild(tr);
    return;
  }
  for (const a of apps) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(a.company || "")}</td>
      <td><a href="${escapeAttr(a.job_url || "#")}" target="_blank">${escapeHtml(a.title || a.job_url || "")}</a></td>
      <td>${escapeHtml(a.status || "")}</td>
    `;
    tbody.appendChild(tr);
  }
}

function escapeHtml(s) {
  return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
function escapeAttr(s) { return escapeHtml(s).replaceAll("`",""); }

async function post(path, body) {
  const token = getToken();
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || `HTTP ${r.status}`);
  return j;
}

async function get(path) {
  const token = getToken();
  const r = await fetch(`${API}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || `HTTP ${r.status}`);
  return j;
}

el("btnSignup").addEventListener("click", async () => {
  setAuthStatus("...");
  try {
    const email = el("email").value;
    const password = el("password").value;
    const j = await post("/auth/signup", { email, password });
    setToken(j.token);
    setAuthStatus("OK (signup)");
  } catch (e) {
    setAuthStatus(e.message);
  }
});

el("btnLogin").addEventListener("click", async () => {
  setAuthStatus("...");
  try {
    const email = el("email").value;
    const password = el("password").value;
    const j = await post("/auth/login", { email, password });
    setToken(j.token);
    setAuthStatus("OK (login)");
  } catch (e) {
    setAuthStatus(e.message);
  }
});

el("btnLogout").addEventListener("click", () => {
  clearToken();
  setAuthStatus("Déconnecté");
});

el("btnCreateBatch").addEventListener("click", async () => {
  setBatchStatus("...");
  try {
    const field = el("field").value;
    const location = el("location").value;
    const job_type = el("jobType").value;
    const j = await post("/batches", { field, location, job_type });
    el("batchId").textContent = j.batchId;
    setBatchStatus("Batch créé. Maintenant fais tourner n8n pour insérer des applications mock.");
  } catch (e) {
    setBatchStatus(e.message);
  }
});

el("btnRefresh").addEventListener("click", async () => {
  setBatchStatus("Refresh...");
  try {
    const batchId = el("batchId").textContent;
    if (!batchId || batchId === "(aucun)") throw new Error("Crée un batch d'abord");
    const j = await get(`/dashboard/${batchId}`);
    renderApps(j.applications);
    setBatchStatus(`OK — applications: ${j.applications.length}`);
  } catch (e) {
    setBatchStatus(e.message);
  }
});

// initial UI
setAuthStatus(getToken() ? "Token présent" : "Pas connecté");
renderApps([]);