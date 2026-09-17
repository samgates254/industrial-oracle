import type {
  AlertPriority,
  DataDomain,
  EvidenceKind,
  FreshnessState,
  SystemState,
} from "@/design-system/tokens";

export type DataSourceKind = "demo" | "api" | "synthetic" | "observed" | "optimized" | "unavailable";

export type Organization = {
  id: string;
  name: string;
  code: string;
};

export type Plant = {
  id: string;
  organizationId: string;
  name: string;
  code: string;
  timezone: string;
};

export type Shift = {
  id: string;
  name: string;
  startedAt: string;
  endsAt: string;
};

export type ConnectivityState = "live" | "degraded" | "offline" | "synthetic";

export type KpiStatus = Extract<
  SystemState,
  "normal" | "warning" | "critical" | "degraded" | "offline"
>;

export type Kpi = {
  id: string;
  label: string;
  value: number;
  unit: string;
  precision: number;
  target: number | null;
  delta: number;
  deltaUnit: string;
  timeContext: string;
  status: KpiStatus;
  domain: DataDomain;
  hierarchy: "primary" | "secondary" | "diagnostic";
  diagnostics?: { label: string; value: string }[];
  sparkline?: number[];
  source: DataSourceKind;
  observedAt: string;
};

export type Bottleneck = {
  id: string;
  location: string;
  process: string;
  kind: string;
  why: string;
  severity: Extract<SystemState, "warning" | "critical" | "degraded">;
  currentRate: number;
  targetRate: number;
  rateUnit: string;
  constraintAsset: string;
  utilizationPct: number;
  economicImpactPerHour: number | null;
  economicImpactNote: string;
  capacityNote: string;
  recommendation: string;
};

export type Alert = {
  id: string;
  priority: AlertPriority;
  title: string;
  summary: string;
  source: string;
  asset: string;
  process: string;
  observedAt: string;
  acknowledged: boolean;
};

export type SeriesPoint = {
  t: string;
  v: number;
};

export type TelemetrySeries = {
  id: string;
  label: string;
  unit: string;
  domain: DataDomain;
  current: number;
  threshold?: { label: string; value: number };
  freshness: FreshnessState;
  observedAt: string;
  points: SeriesPoint[];
};

export type OptimizationSummary = {
  modelId: string;
  modelVersion: string;
  scenarioId: string;
  objective: string;
  solver: string;
  status: "optimal" | "feasible" | "solving" | "failed" | "not-run";
  solveTimeMs: number | null;
  optimalityGapPct: number | null;
  bindingConstraints: string[];
  baselineLabel: string;
  expectedImpact: string;
  decisionVariablesNote: string;
};

export type IntelligenceBlock = {
  kind: EvidenceKind;
  title: string;
  body: string;
};

export type AttentionItem = {
  id: string;
  title: string;
  detail: string;
  status: KpiStatus;
  href: string;
};

export type CommandCenterSnapshot = {
  meta: {
    source: DataSourceKind;
    snapshotAt: string;
    plant: Plant;
    organization: Organization;
    shift: Shift;
    connectivity: ConnectivityState;
    disclaimer: string;
  };
  health: {
    status: Extract<SystemState, "normal" | "warning" | "critical" | "degraded">;
    summary: string;
  };
  kpis: Kpi[];
  bottleneck: Bottleneck | null;
  optimization: OptimizationSummary;
  alerts: Alert[];
  telemetry: TelemetrySeries[];
  attention: AttentionItem[];
  intelligence: IntelligenceBlock[];
};

export type RouteStatus = "live" | "foundation";
