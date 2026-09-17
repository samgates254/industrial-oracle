import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Quality" };

export default function QualityPage() {
  return (
    <PlaceholderScreen
      title="Quality"
      group="Operations"
      summary="No quality lots or inspection plans are loaded. SKU-441 FPY is an advisory on the Command Center only."
      next="Phase 12 — Workforce + Quality."
    />
  );
}
