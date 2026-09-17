import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Analytics" };

export default function AnalyticsPage() {
  return (
    <PlaceholderScreen
      title="Analytics & BI"
      group="Intelligence"
      summary="Historical analysis and saved views are not implemented."
      next="Phase 15 — Analytics."
    />
  );
}
