import type { EvidenceKind } from "./tokens";

/**
 * Locked visual architecture for every Industrial Oracle screen.
 * Physical system → operational state → constraint → consequence →
 * optimization → decision → action.
 *
 * KPI cards must not outrank the constraint.
 */
export const informationHierarchy = [
  "plant-state",
  "exceptions",
  "constraint",
  "optimization",
  "decision",
  "telemetry",
  "deep-dive",
] as const;

export type HierarchyLevel = (typeof informationHierarchy)[number];

export const hierarchyMeta: Record<
  HierarchyLevel,
  { level: number; label: string; role: string }
> = {
  "plant-state": {
    level: 1,
    label: "Plant state",
    role: "Is the plant healthy? What is happening?",
  },
  exceptions: {
    level: 2,
    label: "Active exceptions",
    role: "What is abnormal and unacknowledged?",
  },
  constraint: {
    level: 3,
    label: "Bottleneck / constraint",
    role: "Where is the binding constraint, and why?",
  },
  optimization: {
    level: 4,
    label: "Optimization result",
    role: "What does the solver say? Not observed reality.",
  },
  decision: {
    level: 5,
    label: "Operator decision",
    role: "What action is available, and who must authorize it?",
  },
  telemetry: {
    level: 6,
    label: "Supporting telemetry",
    role: "Trend, threshold, freshness — not the headline.",
  },
  "deep-dive": {
    level: 7,
    label: "Deep-dive data",
    role: "Detail routes and tables. Not the command wall.",
  },
};

export const truthClassMeta: Record<
  EvidenceKind,
  { label: string; note: string; surfaceClass: string; mark: string }
> = {
  "system-fact": {
    label: "System fact",
    note: "Observed measurement",
    surfaceClass: "truth-fact",
    mark: "fact",
  },
  "optimization-result": {
    label: "Optimization result",
    note: "Solver output · not live telemetry",
    surfaceClass: "truth-optimization",
    mark: "opt",
  },
  "ai-interpretation": {
    label: "AI interpretation",
    note: "Non-deterministic · not a control action",
    surfaceClass: "truth-ai",
    mark: "ai",
  },
  "human-decision": {
    label: "Human decision",
    note: "Authorization required",
    surfaceClass: "truth-decision",
    mark: "act",
  },
};

export const plantOverviewContract = {
  visual: "process-topology",
  not: "kpi-grid",
  stages: ["WHERE", "FLOW", "STATE", "CONSTRAINT", "IMPACT"] as const,
};

export const productionContract = {
  visual: "deviation-locator",
  not: "erp-crud",
  stages: [
    "PLAN",
    "SCHEDULE",
    "LINE",
    "MACHINE",
    "OUTPUT",
    "QUALITY",
    "INVENTORY",
  ] as const,
};
