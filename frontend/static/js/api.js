/**
 * NeatAura — API client
 * All fetch calls to the Python/Flask backend go here.
 */

const BASE = "http://localhost:5000/api";

function getToken() { return localStorage.getItem("na_token"); }
function setToken(t) { localStorage.setItem("na_token", t); }
function clearToken() { localStorage.removeItem("na_token"); localStorage.removeItem("na_user"); localStorage.removeItem("na_user_email"); }

function authHeaders() {
  return { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` };
}

async function apiPost(path, body, auth = false) {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: auth ? authHeaders() : { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  return res.json();
}

async function apiGet(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? "?" + qs : ""}`, {
    headers: authHeaders()
  });
  return res.json();
}

async function apiPut(path, body = {}) {
  const res = await fetch(BASE + path, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(body)
  });
  return res.json();
}

// ─── Auth ────────────────────────────────────────────────────
async function register(username, email, password) {
  return apiPost("/register", { username, email, password });
}

async function login(email, password) {
  const data = await apiPost("/login", { email, password });
  if (data.token) {
    setToken(data.token);
    localStorage.setItem("na_user", data.username);
    localStorage.setItem("na_user_email", email); // store real email for profile display
  }
  return data;
}

function logout() { clearToken(); showPage("page-login"); }

// ─── Services ────────────────────────────────────────────────
async function fetchServices() {
  return apiGet("/services");
}

// ─── Workers ─────────────────────────────────────────────────
async function fetchWorkers(serviceId, city) {
  return apiGet("/workers", { service_id: serviceId, city });
}

// ─── Bookings ────────────────────────────────────────────────
async function createBooking(payload) {
  return apiPost("/bookings", payload, true);
}

async function fetchBookings() {
  return apiGet("/bookings");
}

async function cancelBooking(id) {
  return apiPut(`/bookings/${id}/cancel`);
}

// ─── Profile ─────────────────────────────────────────────────
async function fetchProfile() { return apiGet("/profile"); }
async function updateProfile(data) { return apiPut("/profile", data); }