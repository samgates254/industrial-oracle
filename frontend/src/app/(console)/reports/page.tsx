import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Reports" };

export default function ReportsPage() {
  return (
    <PlaceholderScreen
      title="Reports generator"
      group="Control"
      summary="Shift, compliance, and export report generation is not implemented."
      next="Phase 16 — Alerts + Reports."
    />
  );
}
