import type { FreshnessState } from "@/design-system/tokens";
import type {
  Alert,
  Bottleneck,
  ConnectivityState,
  DataSourceKind,
  IntelligenceBlock,
  KpiStatus,
  Plant,
  Organization,
  Shift,
} from "@/types/operational";

export type TopologyNodeKind =
  | "area"
  | "line"
  | "machine"
  | "buffer"
  | "logistics"
  | "energy";

export type FlowKind = "material" | "production" | "energy";

export type TopologyAction = {
  label: string;
  href: string;
  enabled: boolean;
  reason?: string;
};

export type TopologyMetric = {
  label: string;
  value: string;
};

export type TopologyNode = {
  id: string;
  name: string;
  kind: TopologyNodeKind;
  kindLabel: string;
  status: KpiStatus;
  statusNote: string;
  utilizationPct: number | null;
  capacityNote: string | null;
  constraintId: string | null;
  constraintLabel: string | null;
  freshness: FreshnessState;
  observedAt: string;
  metrics: TopologyMetric[];
  actions: TopologyAction[];
};

export type TopologyEdge = {
  id: string;
  from: string;
  to: string;
  flow: FlowKind;
  label: string;
  constrained: boolean;
};

export type TopologyImpact = {
  id: string;
  label: string;
  detail: string;
  status: KpiStatus;
};

export type TopologyCounts = {
  areas: number;
  lines: number;
  machines: number;
  constraints: number;
};

export type PlantTopologySnapshot = {
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
    status: Extract<KpiStatus, "normal" | "warning" | "critical" | "degraded">;
    summary: string;
  };
  counts: TopologyCounts;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  sequence: string[];
  bottleneck: Bottleneck | null;
  impact: TopologyImpact[];
  alerts: Alert[];
  intelligence: IntelligenceBlock[];
};
