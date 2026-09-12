"""Command-line interface (CLI) entrypoint for Industrial Oracle V0.1."""

import argparse
import sys
from typing import List, Optional
import yaml

from industrial_oracle.domain.factory import FactoryConfiguration
from industrial_oracle.validation.exceptions import DomainValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_factory
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.solver.status import SolverStatus
from industrial_oracle.diagnostics.engine import DiagnosticsEngine
from .formatters import format_terminal_summary
from .serializers import serialize_diagnostic_report_to_json


def load_yaml_configuration(path: str) -> dict:
    """Load raw dictionary from YAML file path."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid configuration: Root must be a dictionary, got {type(data).__name__}")
    return data


def parse_and_validate_configuration(data: dict) -> FactoryConfiguration:
    """Execute Level 1 Schema check (forbidding unsupported fields) and Level 2 Physical validation."""
    known_fields = set(FactoryConfiguration.__fields__.keys())
    extra = set(data.keys()) - known_fields
    if extra:
        raise SchemaValidationError(f"Unsupported configuration fields: {sorted(list(extra))}")
    try:
        cfg = FactoryConfiguration.parse_obj(data)
    except Exception as exc:
        raise SchemaValidationError(f"Schema structure error: {exc}") from exc
    validate_factory(cfg)
    return cfg


def execute_validate(config_path: str) -> int:
    """Validate configuration through Level 1 Schema and Level 2 Physical validation."""
    try:
        data = load_yaml_configuration(config_path)
        factory_domain = parse_and_validate_configuration(data)
        print(f"[VALIDATION PASS] Configuration '{config_path}' is structurally and physically valid.")
        print(f"  - Title:    {factory_domain.contract_title}")
        print(f"  - Horizon:  {factory_domain.time_horizon.num_periods} periods (delta_t = {factory_domain.time_horizon.delta_t} h)")
        print(f"  - Entities: {len(factory_domain.resources)} resources, {len(factory_domain.processes)} processes, {len(factory_domain.machines)} machines")
        return 0
    except Exception as exc:
        print(f"[VALIDATION FAIL] {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1


def execute_inspect(config_path: str, show_matrices: bool = False) -> int:
    """Compile mathematical model and inspect canonical dimensions."""
    try:
        data = load_yaml_configuration(config_path)
        factory_domain = parse_and_validate_configuration(data)
        factory = normalize_factory(factory_domain)
        model = ModelCompiler.compile(factory)

        print(f"========================================================================")
        print(f"CANONICAL MODEL INSPECTION: {factory.contract_title}")
        print(f"========================================================================")
        print(f"Variables (N_vars):        {model.num_variables}")
        print(f"Integer Variables (|I|):   {len(model.integer_indices)}")
        print(f"Equality Constraints:      {model.num_equalities}")
        print(f"Inequality Constraints:    {model.num_inequalities}")
        print(f"Fixed Facility Charge:     KSh {model.fixed_charge:,.2f}")
        print(f"Power Factor / Limit:      cos(phi)={factory.electrical.power_factor:.2f} | Limit={factory.electrical.contract_limit_kva:.1f} kVA")

        if show_matrices:
            print(f"------------------------------------------------------------------------")
            print("EQUALITY ROWS (A_eq):")
            for i, row in enumerate(model.A_eq_sparse):
                print(f"  [{i:3d}] {row.equation_id}: {len(row.coefficients)} nonzeros | RHS = {row.rhs}")
            print("INEQUALITY ROWS (A_ub):")
            for i, row in enumerate(model.A_ub_sparse):
                print(f"  [{i:3d}] {row.equation_id}: {len(row.coefficients)} nonzeros | RHS = {row.rhs}")
            print(f"========================================================================")
        return 0
    except Exception as exc:
        print(f"[INSPECTION FAIL] {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1


def execute_run(config_path: str, output_path: Optional[str] = None, time_limit: float = 300.0) -> int:
    """Execute end-to-end optimization pipeline and output diagnostic report."""
    try:
        data = load_yaml_configuration(config_path)
        factory_domain = parse_and_validate_configuration(data)
        factory = normalize_factory(factory_domain)
        model = ModelCompiler.compile(factory)

        solver = HiGHSSolver(time_limit=time_limit)
        result = solver.solve(model)

        report = DiagnosticsEngine.analyze(factory, model, result)
        print(format_terminal_summary(report))

        if output_path:
            json_str = serialize_diagnostic_report_to_json(report, indent=2)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"[REPORT EXPORTED] Diagnostic report saved to '{output_path}'.")

        if result.status == SolverStatus.OPTIMAL:
            return 0
        elif result.status == SolverStatus.INFEASIBLE:
            return 1
        elif result.status in (SolverStatus.TIME_LIMIT, SolverStatus.UNBOUNDED):
            return 2
        else:
            return 3
    except Exception as exc:
        print(f"[EXECUTION ERROR] {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 3


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="industrial-oracle",
        description="Industrial Cost & Optimization Oracle V0.1 — Generic Industrial Energy & Production Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Oracle commands")

    # 1. validate
    val_p = subparsers.add_parser("validate", help="Validate YAML configuration schema and physical sanity")
    val_p.add_argument("config", type=str, help="Path to YAML configuration file")

    # 2. inspect
    ins_p = subparsers.add_parser("inspect", help="Compile canonical model and inspect dimensions/matrices")
    ins_p.add_argument("config", type=str, help="Path to YAML configuration file")
    ins_p.add_argument("--matrices", action="store_true", help="Display sparse row equation details")

    # 3. run
    run_p = subparsers.add_parser("run", help="Solve optimization model and generate diagnostics report")
    run_p.add_argument("config", type=str, help="Path to YAML configuration file")
    run_p.add_argument("-o", "--output", type=str, default=None, help="Path to export JSON diagnostic report")
    run_p.add_argument("--time-limit", type=float, default=300.0, help="Solver time limit in seconds (default: 300.0)")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI main execution entrypoint."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    if parsed.command == "validate":
        return execute_validate(parsed.config)
    elif parsed.command == "inspect":
        return execute_inspect(parsed.config, show_matrices=parsed.matrices)
    elif parsed.command == "run":
        return execute_run(parsed.config, output_path=parsed.output, time_limit=parsed.time_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
