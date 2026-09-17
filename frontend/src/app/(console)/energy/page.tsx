import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Energy" };

export default function EnergyPage() {
  return (
    <PlaceholderScreen
      title="Energy"
      group="Operations"
      summary="Load, contract, and demand-response views are not implemented. Instantaneous demand is on the Command Center."
      next="Phase 10 — Energy."
    />
  );
}
