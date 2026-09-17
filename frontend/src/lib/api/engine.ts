import { ApiError } from "./client";
import type {
  EngineExample,
  EngineInspectResult,
  EngineRunResult,
  EngineValidateResult,
} from "@/types/engine";

export function getEngineUrl(): string {
  const configured = process.env.NEXT_PUBLIC_ENGINE_URL;
  if (configured && configured.length > 0) return configured.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

type EngineErrorBody = {
  detail?: { detail?: string; error_type?: string } | string;
};

async function engineFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getEngineUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Engine is offline. Start it from industrial-oracle with: python -m uvicorn industrial_oracle.web.app:app --port 8000",
      503,
    );
  }

  if (!response.ok) {
    let message = `Engine request failed (${response.status})`;
    try {
      const body = (await response.json()) as EngineErrorBody;
      if (typeof body.detail === "string") message = body.detail;
      else if (body.detail?.detail) message = body.detail.detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export async function getEngineHealth(): Promise<boolean> {
  try {
    const result = await engineFetch<{ status: string }>("/health");
    return result.status === "ok";
  } catch {
    return false;
  }
}

export async function listEngineExamples(): Promise<EngineExample[]> {
  const result = await engineFetch<{ examples: EngineExample[] }>("/api/examples");
  return result.examples;
}

export async function validateEngine(exampleId: string): Promise<EngineValidateResult> {
  return engineFetch("/api/validate", {
    method: "POST",
    body: JSON.stringify({ example_id: exampleId }),
  });
}

export async function inspectEngine(exampleId: string): Promise<EngineInspectResult> {
  return engineFetch("/api/inspect", {
    method: "POST",
    body: JSON.stringify({ example_id: exampleId }),
  });
}

export async function runEngine(exampleId: string): Promise<EngineRunResult> {
  return engineFetch("/api/run", {
    method: "POST",
    body: JSON.stringify({ example_id: exampleId, time_limit: 30 }),
  });
}
