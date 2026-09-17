import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Administration" };

export default function AdminPage() {
  return (
    <PlaceholderScreen
      title="Administration"
      group="System"
      summary="Tenant, plant, and integration administration is not implemented. No fake permissions."
      next="Phase 17 — Administration + Users + Settings."
    />
  );
}
