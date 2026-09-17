/**
 * Typed token catalog. CSS variables in styles/tokens.css are the runtime
 * source; this module documents categories and is used by tests / docs.
 */

export const tokenCategories = [
  "background",
  "border",
  "text",
  "brand",
  "system-state",
  "industrial-data",
  "intelligence",
  "audit",
  "truth-class",
  "information-hierarchy",
  "spacing",
  "typography",
  "radius",
  "elevation",
  "motion",
] as const;

export type TokenCategory = (typeof tokenCategories)[number];

export const systemStates = [
  "normal",
  "success",
  "warning",
  "critical",
  "offline",
  "degraded",
  "maintenance",
] as const;

export type SystemState = (typeof systemStates)[number];

export const dataDomains = [
  "telemetry",
  "production",
  "energy",
  "inventory",
  "logistics",
  "maintenance",
  "quality",
  "optimization",
  "analytics",
] as const;

export type DataDomain = (typeof dataDomains)[number];

export const intelligenceKinds = [
  "recommendation",
  "explanation",
  "uncertainty",
] as const;

export const evidenceKinds = [
  "system-fact",
  "optimization-result",
  "ai-interpretation",
  "human-decision",
] as const;

export type EvidenceKind = (typeof evidenceKinds)[number];

export const alertPriorities = ["P1", "P2", "P3", "P4"] as const;
export type AlertPriority = (typeof alertPriorities)[number];

export const freshnessStates = ["live", "updated", "stale", "offline"] as const;
export type FreshnessState = (typeof freshnessStates)[number];
