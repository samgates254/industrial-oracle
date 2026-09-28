import { afterEach, describe, expect, it, vi } from "vitest";
import {
  backendFetch,
  getBackendToken,
  loginBackend,
  logoutBackend,
} from "./backend";

describe("backend authentication", () => {
  afterEach(() => {
    logoutBackend();
    vi.unstubAllGlobals();
  });

  it("logs in through the real auth endpoint and uses the issued bearer token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: "issued-token",
            token_type: "bearer",
            expires_in: 3600,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "user-id" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await loginBackend("operator@example.test", "a-test-password");
    const profile = await backendFetch<{ id: string }>("/api/v1/users/me");

    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("/api/v1/auth/login");
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({
      email: "operator@example.test",
      password: "a-test-password",
    });
    expect(fetchMock.mock.calls[1]?.[1]?.headers).toMatchObject({
      Authorization: "Bearer issued-token",
    });
    expect(profile.id).toBe("user-id");
  });

  it("does not manufacture or request a demo token when signed out", async () => {
    await expect(getBackendToken()).rejects.toMatchObject({
      status: 401,
      message: "Sign in to access the backend.",
    });
  });
});
