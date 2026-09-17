import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Scenarios" };

export default function ScenariosPage() {
  return (
    <PlaceholderScreen
      title="Scenario laboratory"
      group="Intelligence"
      summary="Baseline vs scenario vs optimized comparison is not implemented. No sliders pretending to solve the plant."
      next="Phase 14 — Scenario Laboratory."
    />
  );
}
