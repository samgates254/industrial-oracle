import { commandCenterDemo } from "@/lib/demo";
import type { CommandCenterSnapshot } from "@/types/operational";
import { ApiError, getDataSource } from "./client";
import { backendFetch } from "./backend";
import { mapOverviewToSnapshot } from "./map-command-center";

export async function getCommandCenter(): Promise<CommandCenterSnapshot> {
  if (getDataSource() === "demo") {
    return commandCenterDemo;
  }

  try {
    const overview = await backendFetch<Parameters<typeof mapOverviewToSnapshot>[0]>(
      "/api/v1/intelligence/command-center/overview?plant_id=P-01",
    );
    return mapOverviewToSnapshot(overview);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("BACKEND UNAVAILABLE", 503);
  }
}
