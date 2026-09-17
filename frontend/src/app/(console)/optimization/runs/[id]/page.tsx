import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Optimization run" };

export default function OptimizationRunPage({ params }: { params: { id: string } }) {
  return (
    <PlaceholderScreen
      title={`Optimization run ${params.id}`}
      group="Intelligence"
      summary="Run detail, input snapshot, and binding-constraint inspection are not implemented."
    />
  );
}
