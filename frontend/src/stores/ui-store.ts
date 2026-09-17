import { create } from "zustand";

export type Density = "compact" | "comfortable";

type UiState = {
  density: Density;
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  commandPaletteOpen: boolean;
  alertCenterOpen: boolean;
  setDensity: (density: Density) => void;
  toggleSidebar: () => void;
  setMobileNavOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setAlertCenterOpen: (open: boolean) => void;
};

export const useUiStore = create<UiState>((set) => ({
  density: "compact",
  sidebarCollapsed: false,
  mobileNavOpen: false,
  commandPaletteOpen: false,
  alertCenterOpen: false,
  setDensity: (density) => set({ density }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setMobileNavOpen: (mobileNavOpen) => set({ mobileNavOpen }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  setAlertCenterOpen: (alertCenterOpen) => set({ alertCenterOpen }),
}));
