export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly correlationId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getDataSource(): "demo" | "api" {
  return process.env.NEXT_PUBLIC_DATA_SOURCE === "api" ? "api" : "demo";
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  if (!base) {
    throw new ApiError(
      "API base URL is not configured. The frontend does not invent backend data.",
      503,
    );
  }

  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  const correlationId =
    response.headers.get("x-correlation-id") ??
    response.headers.get("x-request-id") ??
    undefined;

  if (!response.ok) {
    throw new ApiError(
      `Request failed (${response.status}) for ${path}`,
      response.status,
      correlationId ?? undefined,
    );
  }

  return (await response.json()) as T;
}
