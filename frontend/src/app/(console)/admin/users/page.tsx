import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Users" };

export default function UsersPage() {
  return (
    <PlaceholderScreen
      title="User management"
      group="System"
      summary="Directory and RBAC administration will be backend-authoritative. This screen is a placeholder."
      next="Phase 17 — Administration + Users + Settings."
    />
  );
}
