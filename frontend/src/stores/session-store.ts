import { create } from "zustand";

export type DemoUser = {
  id: string;
  name: string;
  role: string;
  email: string;
};

type SessionState = {
  user: DemoUser;
};

/** Demo identity only. Backend authorization remains authoritative. */
export const useSessionStore = create<SessionState>(() => ({
  user: {
    id: "user_demo_operator",
    name: "A. Mwangi",
    role: "Shift supervisor",
    email: "a.mwangi@demo.industrial-oracle",
  },
}));
