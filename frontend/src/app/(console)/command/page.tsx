import type { Metadata } from "next";
import Link from "next/link";
import { getCommandCenter } from "@/lib/api";
import { CommandCenterView } from "@/features/command-center/command-center-view";
import { ErrorState } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Command Center",
};

export default async function CommandCenterPage() {
  try {
    const snapshot = await getCommandCenter();
    return <CommandCenterView snapshot={snapshot} />;
  } catch {
    return (
      <div className="io-page">
        <ErrorState
          title="BACKEND UNAVAILABLE"
          remaining="API mode does not fall back to demo plant numbers. Start the ZIP backend, then retry."
        />
        <div className="mt-3">
          <Button asChild size="sm">
            <Link href="/command">Retry</Link>
          </Button>
        </div>
      </div>
    );
  }
}
