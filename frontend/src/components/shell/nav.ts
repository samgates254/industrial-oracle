import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bolt,
  Boxes,
  ClipboardCheck,
  Factory,
  FileBarChart,
  Gauge,
  LayoutDashboard,
  Package,
  Settings,
  Shield,
  Truck,
  Users,
  UserCog,
  Wrench,
  FlaskConical,
  Network,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  status: "live" | "foundation";
};

export type NavGroup = {
  id: string;
  label: string;
  items: NavItem[];
};

export const navGroups: NavGroup[] = [
  {
    id: "command",
    label: "Command",
    items: [
      { href: "/command", label: "Overview", icon: LayoutDashboard, status: "live" },
      { href: "/plant", label: "Plant", icon: Factory, status: "live" },
    ],
  },
  {
    id: "operations",
    label: "Operations",
    items: [
      { href: "/production", label: "Production", icon: Gauge, status: "foundation" },
      { href: "/inventory", label: "Inventory", icon: Package, status: "foundation" },
      { href: "/logistics", label: "Logistics", icon: Truck, status: "foundation" },
      { href: "/energy", label: "Energy", icon: Bolt, status: "foundation" },
      { href: "/assets", label: "Assets", icon: Network, status: "foundation" },
      { href: "/maintenance", label: "Maintenance", icon: Wrench, status: "foundation" },
      { href: "/workforce", label: "Workforce", icon: Users, status: "foundation" },
      { href: "/quality", label: "Quality", icon: ClipboardCheck, status: "foundation" },
    ],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    items: [
      { href: "/optimization", label: "Optimization", icon: Activity, status: "live" },
      { href: "/scenarios", label: "Scenarios", icon: FlaskConical, status: "foundation" },
      { href: "/analytics", label: "Analytics", icon: BarChart3, status: "foundation" },
    ],
  },
  {
    id: "control",
    label: "Control",
    items: [
      { href: "/alerts", label: "Alerts", icon: AlertTriangle, status: "foundation" },
      { href: "/reports", label: "Reports", icon: FileBarChart, status: "foundation" },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      { href: "/admin", label: "Administration", icon: Shield, status: "foundation" },
      { href: "/admin/users", label: "Users", icon: UserCog, status: "foundation" },
      { href: "/settings", label: "Settings", icon: Settings, status: "foundation" },
    ],
  },
];

export const allNavItems = navGroups.flatMap((g) => g.items);

export const extraRoutes: NavItem[] = [
  { href: "/login", label: "Login", icon: Shield, status: "live" },
  { href: "/organization", label: "Organization", icon: Boxes, status: "foundation" },
  { href: "/production/orders/WO-4418", label: "Production order", icon: Gauge, status: "foundation" },
  { href: "/assets/M-204", label: "Asset detail", icon: Network, status: "foundation" },
  { href: "/inventory/warehouses/WH-01", label: "Warehouse detail", icon: Package, status: "foundation" },
  { href: "/optimization/runs/OPT-014", label: "Optimization run", icon: Activity, status: "foundation" },
];
