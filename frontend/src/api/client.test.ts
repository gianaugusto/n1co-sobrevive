import { describe, expect, it, vi } from "vitest";
import { ApiError, createApiClient } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("api client", () => {
  it("sends the bearer token and returns the parsed list", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([{ id: "1" }]));
    const api = createApiClient(async () => "tok", "http://api", fetchMock);

    expect(await api.listProcesses()).toEqual([{ id: "1" }]);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/api/v1/processes?limit=100");
    expect(init.headers.Authorization).toBe("Bearer tok");
  });

  it("posts the new process as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "1" }, 201));
    const api = createApiClient(async () => "tok", "http://api", fetchMock);

    await api.createProcess({ tenant_id: "acme", key: "jane", type: "username" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/api/v1/processes");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ tenant_id: "acme", key: "jane", type: "username" });
  });

  it("url-encodes the subscriber name on retry", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "1" }, 202));
    const api = createApiClient(async () => "tok", "http://api", fetchMock);

    await api.retrySubscriber("p1", "billing / eu");

    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://api/api/v1/processes/p1/subscribers/billing%20%2F%20eu/retry",
    );
  });

  it("turns error responses into ApiError with the server detail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ detail: "Not allowed" }, 409));
    const api = createApiClient(async () => "tok", "http://api", fetchMock);

    await expect(api.retrySubscriber("p1", "billing")).rejects.toMatchObject({
      status: 409,
      message: "Not allowed",
    });
    await expect(api.retrySubscriber("p1", "billing")).rejects.toBeInstanceOf(ApiError);
  });

  it("falls back to a generic message when the error body is not JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("boom", { status: 500 }));
    const api = createApiClient(async () => "tok", "http://api", fetchMock);

    await expect(api.listProcesses()).rejects.toThrow("Request failed (500)");
  });
});
