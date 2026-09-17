export type EngineExample = {
  id: string;
  tier: "supported" | "supported_with_limitations" | "unsupported";
  path: string;
  contract_title: string | null;
  schema_version: string | null;
  freeze_vector: string | null;
};

export type EngineValidateResult = {
  status: "success";
  contract_title: string;
  schema_version: string;
  freeze_vector: string;
  horizon: { num_periods: number; delta_t: number };
  entities: { resources: number; processes: number; machines: number };
};

export type EngineInspectResult = {
  status: "success";
  contract_title: string;
  schema_version: string;
  freeze_vector: string;
  num_variables: number;
  num_integer_variables: number;
  num_equalities: number;
  num_inequalities: number;
  fixed_charge: number;
  equality_ids: string[];
  inequality_ids: string[];
};

export type EngineBindingConstraint = {
  equation_id: string;
  category: string;
  state: string;
  slack: number;
  lhs_value: number;
  rhs_value: number;
  description: string;
};

export type EngineEconomics = {
  energy_variable: number;
  energy_fixed: number;
  demand_charge: number;
  purchase: number;
  startup: number;
  holding: number;
  shortfall: number;
  fixed_charge: number;
  total_cost: number;
  reconstruction_residual: number;
  percentage_shares: Record<string, number>;
};

export type EngineMachineOps = {
  machine_id: string;
  average_utilization: number;
  operating_hours: number;
  total_startups: number;
};

export type EngineResourceFlow = {
  resource_id: string;
  initial_stock: number;
  total_receipts: number;
  total_produced: number;
  total_consumed: number;
  total_shipped: number;
  final_stock: number;
  conservation_residual: number;
};

export type EngineRunResult = {
  status: "success";
  contract_title: string;
  schema_version: string;
  freeze_vector: string;
  solver_name: string;
  solver_status: string;
  termination_message: string;
  objective_value: number | null;
  solve_time_seconds: number;
  model: {
    num_variables: number;
    num_integer_variables: number;
    num_equalities: number;
    num_inequalities: number;
  };
  report: {
    factory_name: string;
    solver_status: string;
    solve_time_seconds: number;
    feasibility: {
      is_verified_feasible: boolean;
      max_violation: number;
    };
    binding_constraints: EngineBindingConstraint[];
    peak_setting_periods: number[];
    economics: EngineEconomics;
    operations: Record<string, EngineMachineOps>;
    resource_flows: Record<string, EngineResourceFlow>;
    infeasibility: {
      is_infeasible: boolean;
      evidence_messages: string[];
    };
  };
};
