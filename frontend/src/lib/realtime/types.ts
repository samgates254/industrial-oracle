/**
 * Transport-agnostic realtime contracts.
 * Do not invent a backend. Connect SSE/WebSocket implementations later.
 */

export type TelemetryEvent = {
  type: "telemetry";
  seriesId: string;
  value: number;
  observedAt: string;
};

export type AlertEvent = {
  type: "alert";
  alertId: string;
  observedAt: string;
};

export type OptimizationJobEvent = {
  type: "optimization-job";
  runId: string;
  status: "queued" | "solving" | "optimal" | "feasible" | "failed";
  observedAt: string;
};

export type RealtimeEvent = TelemetryEvent | AlertEvent | OptimizationJobEvent;

export type RealtimeHandle = {
  disconnect: () => void;
};

export type RealtimeClient = {
  connect: (onEvent: (event: RealtimeEvent) => void) => RealtimeHandle;
};
