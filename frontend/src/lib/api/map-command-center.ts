import type {
  Alert,
  Bottleneck,
  CommandCenterSnapshot,
  IntelligenceBlock,
  Kpi,
  OptimizationSummary,
} from "@/types/operational";
import type { PlantTopologySnapshot, TopologyNode } from "@/types/topology";

type Overview = {
  plant_id: string;
  tenant_id: string;
  is_synthetic: boolean;
  demo_banner: string;
  operational_state: {
    primary_line_id: string | null;
    line_status: string;
    plant_status: string;
    target_throughput: number | null;
    actual_throughput: number | null;
    throughput_deviation: number | null;
    bottleneck_asset_id: string | null;
    active_machine_count: number;
    total_events_processed: number;
    oee: { overall: number; availability: number; performance: number; quality: number };
    energy: { current_power_kw: number; current_power_mw: number; total_energy_kwh: number };
    inventory_buffers: { material_id: string; on_hand: number; buffer_hours: number }[];
    alerts: { alert_id: string; severity: string; title: string; description: string; entity_id: string; detected_at: string; type: string }[];
  };
  active_constraints: {
    constraint_id: string;
    type: string;
    severity: string;
    entity_id: string;
    title: string;
    description: string;
    observed_value: number;
    required_value: number | null;
    unit: string;
    evidence: Record<string, unknown>;
  }[];
  pending_decisions: {
    decision_id: string;
    title: string;
    status: string;
    recommendation: { description: string; target_entity_id: string };
    expected_effect: { throughput_delta: number; cost_delta_estimate: number | null };
  }[];
  m816_optimization: {
    solver_status: string | null;
    objective_value: number | null;
    throughput_delta: number | null;
    solver_name: string | null;
    solve_time_ms?: number | null;
    message?: string | null;
  };
  truth?: { source: string; connectivity: string };
};

function mapSolverStatus(raw: string | null | undefined): OptimizationSummary["status"] {
  const v = (raw || "NOT_RUN").toUpperCase();
  if (v === "OPTIMAL") return "optimal";
  if (v === "FEASIBLE") return "feasible";
  if (v === "NOT_RUN") return "not-run";
  return "failed";
}

function healthFromPlant(status: string): CommandCenterSnapshot["health"]["status"] {
  if (status === "STOPPED") return "critical";
  if (status === "DEGRADED") return "warning";
  if (status === "IDLE") return "degraded";
  return "normal";
}

export function mapOverviewToSnapshot(overview: Overview): CommandCenterSnapshot {
  const ops = overview.operational_state;
  const now = new Date().toISOString();
  const source = overview.is_synthetic ? "synthetic" : "api";
  const bottleneckCst = overview.active_constraints.find((c) => c.type === "capacity_bottleneck") ?? overview.active_constraints[0];
  const pending = overview.pending_decisions[0];
  const opt = overview.m816_optimization;

  const kpis: Kpi[] = [
    {
      id: "oee",
      label: "Plant OEE",
      value: ops.oee.overall,
      unit: "%",
      precision: 1,
      target: null,
      delta: 0,
      deltaUnit: "pp",
      timeContext: "From projected events",
      status: ops.oee.overall < 85 ? "warning" : "normal",
      domain: "production",
      hierarchy: "primary",
      diagnostics: [
        { label: "Availability", value: `${ops.oee.availability}%` },
        { label: "Performance", value: `${ops.oee.performance}%` },
        { label: "Quality", value: `${ops.oee.quality}%` },
      ],
      source,
      observedAt: now,
    },
    {
      id: "throughput",
      label: "Throughput",
      value: ops.actual_throughput ?? 0,
      unit: "pcs/h",
      precision: 0,
      target: ops.target_throughput,
      delta: ops.throughput_deviation ?? 0,
      deltaUnit: "pcs/h",
      timeContext: "Binding line",
      status: (ops.throughput_deviation ?? 0) < 0 ? "warning" : "normal",
      domain: "production",
      hierarchy: "primary",
      source,
      observedAt: now,
    },
    {
      id: "demand",
      label: "Electrical demand",
      value: ops.energy.current_power_mw,
      unit: "MW",
      precision: 3,
      target: null,
      delta: 0,
      deltaUnit: "MW",
      timeContext: "Last energy_reading",
      status: "normal",
      domain: "energy",
      hierarchy: "primary",
      source,
      observedAt: now,
    },
    {
      id: "inventory",
      label: "Inventory on hand",
      value: ops.inventory_buffers[0]?.on_hand ?? 0,
      unit: "u",
      precision: 0,
      target: null,
      delta: 0,
      deltaUnit: "u",
      timeContext: ops.inventory_buffers[0]?.material_id ?? "no movements",
      status: "normal",
      domain: "inventory",
      hierarchy: "secondary",
      source,
      observedAt: now,
    },
  ];

  const bottleneck: Bottleneck | null = bottleneckCst
    ? {
        id: bottleneckCst.constraint_id,
        location: String(bottleneckCst.evidence?.line_id ?? ops.primary_line_id ?? "line"),
        process: bottleneckCst.type,
        kind: "Capacity constraint",
        why: bottleneckCst.description,
        severity: bottleneckCst.severity === "CRITICAL" ? "critical" : "warning",
        currentRate: bottleneckCst.observed_value,
        targetRate: bottleneckCst.required_value ?? 0,
        rateUnit: bottleneckCst.unit || "pcs/h",
        constraintAsset: bottleneckCst.entity_id,
        utilizationPct: 0,
        economicImpactPerHour: pending?.expected_effect.cost_delta_estimate ?? null,
        economicImpactNote: "Not computed unless costs were used in the solve",
        capacityNote: `Evidence: ${JSON.stringify(bottleneckCst.evidence)}`,
        recommendation: pending?.recommendation.description ?? "No decision pending",
      }
    : null;

  const solverOk = opt.solver_status === "OPTIMAL" || opt.solver_status === "FEASIBLE";
  const optimization: OptimizationSummary = {
    modelId: solverOk ? "M8.16" : "—",
    modelVersion: "frozen",
    scenarioId: overview.plant_id,
    objective: opt.objective_value != null ? `objective ${opt.objective_value}` : "not calculated",
    solver: opt.solver_name ?? "not invoked",
    status: mapSolverStatus(opt.solver_status),
    solveTimeMs: opt.solve_time_ms ?? null,
    optimalityGapPct: solverOk ? 0 : null,
    bindingConstraints: overview.active_constraints.map((c) => c.constraint_id),
    baselineLabel: "Projected operational state",
    expectedImpact:
      opt.throughput_delta != null
        ? `Throughput delta ${opt.throughput_delta} pcs/h (solver ${opt.solver_status})`
        : opt.message ?? "No solver result",
    decisionVariablesNote: pending
      ? `${pending.title} (${pending.status})`
      : "No pending decision",
  };

  const alerts: Alert[] = ops.alerts.map((a) => ({
    id: a.alert_id,
    priority: a.severity === "CRITICAL" ? "P1" : "P2",
    title: a.title,
    summary: a.description,
    source: a.type,
    asset: a.entity_id,
    process: a.type,
    observedAt: a.detected_at || now,
    acknowledged: false,
  }));

  const intelligence: IntelligenceBlock[] = [
    {
      kind: "system-fact",
      title: "System fact",
      body: `${ops.total_events_processed} events projected. Line ${ops.primary_line_id ?? "—"} ${ops.actual_throughput ?? "n/a"} pcs/h vs target ${ops.target_throughput ?? "n/a"}.`,
    },
    {
      kind: "optimization-result",
      title: "Optimization result",
      body: `Solver ${opt.solver_name ?? "none"} status ${opt.solver_status ?? "NOT_RUN"}. ${opt.message ?? ""}`,
    },
    {
      kind: "ai-interpretation",
      title: "AI interpretation",
      body: "Not generated. This screen does not invent causal narrative.",
    },
    {
      kind: "human-decision",
      title: "Human decision",
      body: pending
        ? `${pending.title}. Status ${pending.status}. AI cannot dispatch the plant.`
        : "No pending authorization.",
    },
  ];

  return {
    meta: {
      source,
      snapshotAt: now,
      organization: {
        id: overview.tenant_id,
        name: "Synthetic tenant",
        code: "SYN",
      },
      plant: {
        id: overview.plant_id,
        organizationId: overview.tenant_id,
        name: `Plant ${overview.plant_id}`,
        code: overview.plant_id,
        timezone: "UTC",
      },
      shift: {
        id: "synthetic-horizon",
        name: "Synthetic run",
        startedAt: now,
        endsAt: now,
      },
      connectivity: overview.is_synthetic ? "synthetic" : "degraded",
      disclaimer: overview.demo_banner,
    },
    health: {
      status: healthFromPlant(ops.plant_status),
      summary:
        ops.total_events_processed === 0
          ? "No events projected. Run the synthetic simulator from Optimization."
          : `Plant ${ops.plant_status}. ${ops.total_events_processed} events. Binding ${ops.bottleneck_asset_id ?? "none"}.`,
    },
    kpis,
    bottleneck,
    optimization,
    alerts,
    telemetry: [],
    attention: pending
      ? [
          {
            id: pending.decision_id,
            title: pending.title,
            detail: pending.recommendation.description,
            status: "warning",
            href: "/optimization",
          },
        ]
      : [],
    intelligence,
  };
}

type TopologyPayload = {
  plant_id: string;
  tenant_id: string;
  is_synthetic: boolean;
  source: string;
  snapshot_at: string | null;
  processed_event_count: number;
  nodes: TopologyNode[];
  edges: PlantTopologySnapshot["edges"];
  sequence: string[];
  counts: PlantTopologySnapshot["counts"];
};

export function mapTopologyToSnapshot(
  payload: TopologyPayload,
  command: CommandCenterSnapshot,
): PlantTopologySnapshot {
  return {
    meta: {
      ...command.meta,
      disclaimer: command.meta.disclaimer,
    },
    health: command.health,
    counts: payload.counts,
    nodes: payload.nodes,
    edges: payload.edges,
    sequence: payload.sequence,
    bottleneck: command.bottleneck,
    impact: command.bottleneck
      ? [
          {
            id: "imp_cap",
            label: "Capacity reduced",
            detail: `${command.bottleneck.currentRate} vs ${command.bottleneck.targetRate} ${command.bottleneck.rateUnit}`,
            status: "warning",
          },
        ]
      : [],
    alerts: command.alerts,
    intelligence: command.intelligence.filter(
      (b) => b.kind === "optimization-result" || b.kind === "ai-interpretation",
    ),
  };
}
