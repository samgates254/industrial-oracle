import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Production order" };

export default function ProductionOrderPage({ params }: { params: { id: string } }) {
  return (
    <PlaceholderScreen
      title={`Production order ${params.id}`}
      group="Operations"
      summary="Order routing, bill of materials, and execution state are not implemented. This route exists so order deep-links from Command Center are real."
    />
  );
}
