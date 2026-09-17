import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Assets" };

export default function AssetsPage() {
  return (
    <PlaceholderScreen
      title="Asset management"
      group="Operations"
      summary="Asset registry, hierarchy, and condition views are not implemented."
      next="Phase 11 — Assets + Maintenance."
    />
  );
}
