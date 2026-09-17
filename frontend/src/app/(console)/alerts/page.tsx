import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Alerts" };

export default function AlertsPage() {
  return (
    <PlaceholderScreen
      title="Alerts & notifications"
      group="Control"
      summary="The full alert queue, acknowledge, and escalate flows are not implemented. Unacknowledged P2 items appear on Command Center and in the shell alert center."
      next="Phase 16 — Alerts + Reports."
    />
  );
}
