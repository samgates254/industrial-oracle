import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Maintenance" };

export default function MaintenancePage() {
  return (
    <PlaceholderScreen
      title="Maintenance"
      group="Operations"
      summary="Work orders, PM compliance, and spare-parts demand are not implemented."
      next="Phase 11 — Assets + Maintenance."
    />
  );
}
