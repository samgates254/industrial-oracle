import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Workforce" };

export default function WorkforcePage() {
  return (
    <PlaceholderScreen
      title="Workforce"
      group="Operations"
      summary="Roster, skills, and attendance views are not implemented."
      next="Phase 12 — Workforce + Quality."
    />
  );
}
