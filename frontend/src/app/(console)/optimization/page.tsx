import type { Metadata } from "next";
import { EngineWorkspace } from "@/features/optimization/engine-workspace";

export const metadata: Metadata = { title: "Optimization" };

export default function OptimizationPage() {
  return <EngineWorkspace />;
}
