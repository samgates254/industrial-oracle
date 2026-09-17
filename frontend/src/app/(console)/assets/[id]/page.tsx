import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Asset" };

export default function AssetDetailPage({ params }: { params: { id: string } }) {
  return (
    <PlaceholderScreen
      title={`Asset ${params.id}`}
      group="Operations"
      summary="Asset telemetry history, work orders, and spare parts are not implemented. M-204 is referenced from the Command Center bottleneck."
    />
  );
}
