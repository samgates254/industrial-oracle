import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <PlaceholderScreen
      title="System settings"
      group="System"
      summary="Operator preferences beyond density (in the shell) are not implemented."
      next="Phase 17 — Administration + Users + Settings."
    />
  );
}
