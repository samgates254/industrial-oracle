import { ApiError } from "./client";

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && configured.length > 0) return configured.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

type TokenResponse = { access_token: string; token_type: string; expires_in: number };

let cachedToken: string | null = null;

function saveToken(token: string): void {
  cachedToken = token;
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem("industrial-oracle-access-token", token);
  }
}

export async function loginBackend(email: string, password: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });
  } catch {
    throw new ApiError("Backend unavailable. Check the configured API URL.", 503);
  }
  if (!response.ok) {
    throw new ApiError(`Sign-in failed (${response.status}).`, response.status);
  }

  const body = (await response.json()) as TokenResponse;
  if (!body.access_token || body.token_type.toLowerCase() !== "bearer") {
    throw new ApiError("The backend returned an invalid authentication response.", 502);
  }
  saveToken(body.access_token);
}

export function logoutBackend(): void {
  cachedToken = null;
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem("industrial-oracle-access-token");
  }
}

export async function getBackendToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  if (typeof window !== "undefined") {
    const storedToken = window.sessionStorage.getItem("industrial-oracle-access-token");
    if (storedToken) {
      cachedToken = storedToken;
      return storedToken;
    }
  }
  throw new ApiError("Sign in to access the backend.", 401);
}

export async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  const token = await getBackendToken();
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError("BACKEND UNAVAILABLE", 503);
  }

  const correlationId =
    response.headers.get("x-request-id") ?? response.headers.get("x-correlation-id") ?? undefined;

  if (!response.ok) {
    throw new ApiError(
      `Backend request failed (${response.status}) for ${path}`,
      response.status,
      correlationId,
    );
  }
  return (await response.json()) as T;
}

export async function runSyntheticSimulation(plantId = "P-01"): Promise<Record<string, unknown>> {
  return backendFetch(`/api/v1/events/simulation/run?plant_id=${encodeURIComponent(plantId)}`, {
    method: "POST",
  });
}

export async function authorizeDecision(decisionId: string, approve: boolean) {
  return backendFetch(`/api/v1/intelligence/decisions/${encodeURIComponent(decisionId)}/authorize`, {
    method: "POST",
    body: JSON.stringify({ approve }),
  });
}

export async function executeDecision(decisionId: string) {
  return backendFetch(`/api/v1/intelligence/decisions/${encodeURIComponent(decisionId)}/execute`, {
    method: "POST",
  });
}
