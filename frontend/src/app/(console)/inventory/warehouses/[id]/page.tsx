import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";

export const metadata: Metadata = { title: "Warehouse" };

export default function WarehousePage({ params }: { params: { id: string } }) {
  return (
    <PlaceholderScreen
      title={`Warehouse ${params.id}`}
      group="Operations"
      summary="Warehouse layout, locations, and movements are not implemented."
    />
  );
}
