import type { Metadata } from "next";
import { PlaceholderScreen } from "@/features/placeholders/placeholder-screen";
import { productionContract } from "@/design-system/visual-architecture";

export const metadata: Metadata = { title: "Production" };

export default function ProductionPage() {
  return (
    <PlaceholderScreen
      title="Production"
      group="Operations"
      summary="This screen will locate production deviation along plan → schedule → line → machine → output. It will not be a generic ERP order list."
      next="Not in this task. Visual contract is locked before implementation."
      intent={{
        visual: productionContract.visual,
        not: productionContract.not,
        stages: productionContract.stages,
      }}
    />
  );
}
