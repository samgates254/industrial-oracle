import { plantTopologyDemo } from "@/lib/demo/plant-topology";
import type { PlantTopologySnapshot } from "@/types/topology";
import { ApiError, getDataSource } from "./client";
import { backendFetch } from "./backend";
import { getCommandCenter } from "./command";
import { mapTopologyToSnapshot } from "./map-command-center";

export async function getPlantTopology(): Promise<PlantTopologySnapshot> {
  if (getDataSource() === "demo") {
    return plantTopologyDemo;
  }

  try {
    const [command, topology] = await Promise.all([
      getCommandCenter(),
      backendFetch<Parameters<typeof mapTopologyToSnapshot>[0]>(
        "/api/v1/intelligence/plant/topology?plant_id=P-01",
      ),
    ]);
    return mapTopologyToSnapshot(topology, command);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("BACKEND UNAVAILABLE", 503);
  }
}
