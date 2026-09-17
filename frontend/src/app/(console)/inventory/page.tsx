import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Inventory" };

export default function InventoryPage() {
  return (
    <PlaceholderScreen
      title="Inventory"
      group="Operations"
      summary="No released inventory views exist yet. Buffer cover and warehouse detail will be implemented in Phase 8."
      next="Phase 8 — Inventory."
    />
  );
}
