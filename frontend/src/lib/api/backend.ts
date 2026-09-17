import { ApiError } from "./client";

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && configured.length > 0) return configured.replace(/\/$/, "");
  return "http://127.0.0.1:8001";
}

type TokenResponse = { access_token: string; token_type: string };

let cachedToken: string | null = null;

export async function getBackendToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  const base = getApiBaseUrl();
  let response: Response;
  try {
    response = await fetch(`${base}/api/v1/auth/demo-token`, {
      method: "POST",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "BACKEND UNAVAILABLE. Start _zip_backend with: python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000",
      503,
    );
  }
  if (!response.ok) {
    throw new ApiError(`Auth failed (${response.status})`, response.status);
  }
  const body = (await response.json()) as TokenResponse;
  cachedToken = body.access_token;
  return cachedToken;
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
