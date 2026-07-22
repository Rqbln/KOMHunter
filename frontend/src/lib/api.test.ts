import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { healthCheck, auth, ApiError } from "./api";

interface CapturedCall {
  url: string;
  init: RequestInit;
}

const originalFetch = globalThis.fetch;
let calls: CapturedCall[] = [];

/** Install a fetch mock that records calls and returns responses built per call */
function mockFetch(makeResponse: () => Response) {
  const fake = async (input: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(input), init: init ?? {} });
    return makeResponse();
  };
  globalThis.fetch = fake as unknown as typeof fetch;
}

function jsonResponse(
  body: unknown,
  status = 200,
  extraHeaders: Record<string, string> = {}
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...extraHeaders },
  });
}

function capturedHeaders(call: CapturedCall): Record<string, string> {
  return (call.init.headers ?? {}) as Record<string, string>;
}

beforeEach(() => {
  calls = [];
  localStorage.clear();
});

afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("fetchAPI authorization header", () => {
  it("omits Authorization when no kom_token is stored", async () => {
    mockFetch(() => jsonResponse({ status: "ok" }));

    await healthCheck();

    expect(calls).toHaveLength(1);
    expect(capturedHeaders(calls[0])["Authorization"]).toBeUndefined();
  });

  it("attaches Authorization: Bearer <token> when kom_token is stored", async () => {
    localStorage.setItem("kom_token", "my-session-jwt");
    mockFetch(() => jsonResponse({ status: "ok" }));

    await healthCheck();

    expect(capturedHeaders(calls[0])["Authorization"]).toBe(
      "Bearer my-session-jwt"
    );
  });
});

describe("fetchAPI refreshed-token handling", () => {
  it("stores the X-KOM-Refreshed-Token response header as kom_token", async () => {
    localStorage.setItem("kom_token", "old-jwt");
    mockFetch(() =>
      jsonResponse({ status: "ok" }, 200, {
        "X-KOM-Refreshed-Token": "re-minted-jwt",
      })
    );

    await healthCheck();

    expect(localStorage.getItem("kom_token")).toBe("re-minted-jwt");
  });

  it("leaves kom_token untouched when the header is absent", async () => {
    localStorage.setItem("kom_token", "old-jwt");
    mockFetch(() => jsonResponse({ status: "ok" }));

    await healthCheck();

    expect(localStorage.getItem("kom_token")).toBe("old-jwt");
  });
});

describe("fetchAPI error handling", () => {
  it("throws ApiError with status and backend detail message", async () => {
    mockFetch(() =>
      jsonResponse(
        { detail: "Invalid or expired session - please log in with Strava again" },
        401
      )
    );

    let caught: unknown;
    try {
      await healthCheck();
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    const apiError = caught as ApiError;
    expect(apiError.status).toBe(401);
    expect(apiError.message).toBe(
      "Invalid or expired session - please log in with Strava again"
    );
  });

  it("falls back to a generic message when the error body is not JSON", async () => {
    mockFetch(() => new Response("boom", { status: 502 }));

    let caught: unknown;
    try {
      await healthCheck();
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect((caught as ApiError).status).toBe(502);
  });
});

describe("auth.refreshSession", () => {
  it("POSTs {token} to /api/auth/refresh and returns the new session token", async () => {
    mockFetch(() => jsonResponse({ token: "new-jwt" }));

    const result = await auth.refreshSession("old-jwt");

    expect(calls).toHaveLength(1);
    expect(calls[0].url.endsWith("/api/auth/refresh")).toBe(true);
    expect(calls[0].init.method).toBe("POST");
    expect(JSON.parse(calls[0].init.body as string)).toEqual({
      token: "old-jwt",
    });
    expect(result).toEqual({ token: "new-jwt" });
  });
});
