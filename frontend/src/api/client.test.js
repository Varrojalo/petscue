import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, request } from "./client";

function respond(status, body) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(body === undefined ? null : JSON.stringify(body), { status }));
}

describe("request", () => {
  afterEach(() => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  it("adds query parameters and skips empty ones", async () => {
    const fetch = respond(200, { items: [] });
    await request("/public/animals", { params: { species: 1, size: "", page: 2 } });
    expect(String(fetch.mock.calls[0][0])).toMatch(/\/api\/public\/animals\?species=1&page=2$/);
  });

  it("sends JSON with the CSRF token on changes", async () => {
    document.cookie = "csrftoken=abc123";
    const fetch = respond(201, { ok: true });
    await request("/dashboard/traits", { method: "POST", body: { label: "Sociable" } });
    const [, options] = fetch.mock.calls[0];
    expect(options.headers["X-CSRFToken"]).toBe("abc123");
    expect(options.body).toBe('{"label":"Sociable"}');
  });

  it("turns backend errors into messages per field", async () => {
    respond(422, { detail: "Revisa los datos enviados.", errors: [{ field: "rut", message: "RUT no válido." }] });
    const error = await request("/public/applications", { method: "POST", body: {} }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.detail).toBe("Revisa los datos enviados.");
    expect(error.fieldErrors).toEqual({ rut: "RUT no válido." });
  });

  it("explains connection problems in plain words", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    const error = await request("/public/stats").catch((e) => e);
    expect(error.status).toBe(0);
    expect(error.detail).toMatch(/No pudimos conectarnos/);
  });

  it("returns nothing on 204", async () => {
    respond(204);
    await expect(request("/auth/logout", { method: "POST" })).resolves.toBeNull();
  });
});
