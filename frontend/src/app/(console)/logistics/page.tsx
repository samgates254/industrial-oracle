import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Logistics" };

export default function LogisticsPage() {
  return (
    <PlaceholderScreen
      title="Logistics"
      group="Operations"
      summary="Dock schedule, carrier status, and yard occupancy will be implemented in Phase 9. Command Center shows dock utilization only."
      next="Phase 9 — Logistics."
    />
  );
}
