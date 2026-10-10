/**
 * The only place that talks to the backend. Every request goes through `request`, which:
 * - sends and reads JSON (or a FormData when uploading files),
 * - includes the session cookie and, on changes, the CSRF token,
 * - turns errors into an ApiError with the backend's Spanish message.
 */

export class ApiError extends Error {
  constructor(status, detail, errors = []) {
    super(detail);
    this.status = status;
    this.detail = detail;
    // { fieldName: "message" } so forms can show each message next to its field
    this.fieldErrors = Object.fromEntries(errors.filter((e) => e.field).map((e) => [e.field, e.message]));
  }
}

function readCookie(name) {
  const match = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

export async function request(path, { method = "GET", body, form, params } = {}) {
  const url = new URL(`/api${path}`, window.location.origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  });

  const headers = { Accept: "application/json" };
  if (method !== "GET") {
    const token = readCookie("csrftoken");
    if (token) headers["X-CSRFToken"] = token;
  }
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, { method, headers, body: payload, credentials: "same-origin" });
  } catch {
    throw new ApiError(0, "No pudimos conectarnos. Revisa tu conexión a internet e intenta de nuevo.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, data.detail || "Algo salió mal. Intenta de nuevo en unos minutos.", data.errors);
  }
  return data;
}
