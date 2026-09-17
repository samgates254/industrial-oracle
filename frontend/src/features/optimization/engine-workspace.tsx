"use client";

import { useEffect, useMemo, useState } from "react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel, SectionHeader } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { TruthClassLabel, TruthFrame } from "@/components/industrial/truth-class";
import { ApiError } from "@/lib/api/client";
import { formatNumber } from "@/lib/format";
import {
  inspectEngine,
  listEngineExamples,
  runEngine,
  validateEngine,
} from "@/lib/api/engine";
import type {
  EngineExample,
  EngineInspectResult,
  EngineRunResult,
  EngineValidateResult,
} from "@/types/engine";
import { EngineStatus } from "./engine-status";
import { LoopWorkspace } from "./loop-workspace";

function ksh(value: number): string {
  return `KSh ${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Engine request failed.";
}

export function EngineWorkspace() {
  const [examples, setExamples] = useState<EngineExample[]>([]);
  const [exampleId, setExampleId] = useState("manufacturing_metals");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"validate" | "inspect" | "run" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [validated, setValidated] = useState<EngineValidateResult | null>(null);
  const [inspected, setInspected] = useState<EngineInspectResult | null>(null);
  const [run, setRun] = useState<EngineRunResult | null>(null);

  useEffect(() => {
    listEngineExamples()
      .then((items) => {
        setExamples(items);
        setLoadError(null);
      })
      .catch((error: unknown) => {
        setLoadError(errorMessage(error));
      });
  }, []);

  const selected = useMemo(
    () => examples.find((item) => item.id === exampleId) ?? null,
    [examples, exampleId],
  );

  function resetResults() {
    setValidated(null);
    setInspected(null);
    setRun(null);
    setActionError(null);
  }

  async function onValidate() {
    setBusy("validate");
    setActionError(null);
    try {
      const result = await validateEngine(exampleId);
      setValidated(result);
    } catch (error) {
      setValidated(null);
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function onInspect() {
    setBusy("inspect");
    setActionError(null);
    try {
      const result = await inspectEngine(exampleId);
      setInspected(result);
    } catch (error) {
      setInspected(null);
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function onRun() {
    setBusy("run");
    setActionError(null);
    try {
      const result = await runEngine(exampleId);
      setRun(result);
    } catch (error) {
      setRun(null);
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  const items = examples.map((item) => ({
    value: item.id,
    label: `${item.contract_title ?? item.id} (${item.tier})`,
  }));

  return (
    <div className="io-page flex flex-col gap-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Breadcrumbs
            items={[
              { href: "/command", label: "Command" },
              { label: "Optimization" },
            ]}
          />
          <h1 className="type-page-title mt-1">Optimization engine</h1>
          <p className="type-secondary mt-1">
            Live HiGHS solve of bundled factory YAML. This is not the Athi River demo snapshot.
          </p>
        </div>
        <EngineStatus />
      </header>

      <LoopWorkspace />

      <Panel>
        <SectionHeader
          eyebrow="Factory pack"
          title="Select a configuration and run the frozen compiler"
        />
        {loadError ? (
          <p className="type-body text-state-warning">{loadError}</p>
        ) : (
          <div className="flex flex-col gap-3">
            <Select
              ariaLabel="Factory example"
              value={exampleId}
              onValueChange={(value) => {
                setExampleId(value);
                resetResults();
              }}
              items={
                items.length
                  ? items
                  : [{ value: exampleId, label: exampleId }]
              }
              className="max-w-xl"
            />
            {selected ? (
              <p className="type-meta text-muted">
                {selected.path} · freeze {selected.freeze_vector ?? "—"} · schema{" "}
                {selected.schema_version ?? "—"}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2">
              <Button size="sm" disabled={busy !== null} onClick={() => void onValidate()}>
                {busy === "validate" ? "Validating…" : "Validate"}
              </Button>
              <Button size="sm" disabled={busy !== null} onClick={() => void onInspect()}>
                {busy === "inspect" ? "Compiling…" : "Inspect model"}
              </Button>
              <Button
                size="sm"
                variant="optimize"
                disabled={busy !== null}
                onClick={() => void onRun()}
              >
                {busy === "run" ? "Solving…" : "Run HiGHS"}
              </Button>
            </div>
          </div>
        )}
        {actionError ? <p className="type-body mt-3 text-state-warning">{actionError}</p> : null}
      </Panel>

      {validated ? (
        <Panel>
          <SectionHeader eyebrow="Validation" title={validated.contract_title} />
          <Badge tone="normal">Schema and physical checks passed</Badge>
          <dl className="io-readout mt-3">
            <dt>Horizon</dt>
            <dd>
              {validated.horizon.num_periods} periods · Δt {validated.horizon.delta_t} h
            </dd>
            <dt>Resources</dt>
            <dd>{validated.entities.resources}</dd>
            <dt>Processes</dt>
            <dd>{validated.entities.processes}</dd>
            <dt>Machines</dt>
            <dd>{validated.entities.machines}</dd>
            <dt>Freeze</dt>
            <dd>{validated.freeze_vector}</dd>
          </dl>
        </Panel>
      ) : null}

      {inspected ? (
        <Panel>
          <SectionHeader eyebrow="Canonical model" title="Compiled dimensions" />
          <dl className="io-readout mt-3">
            <dt>Variables</dt>
            <dd>{inspected.num_variables}</dd>
            <dt>Integer</dt>
            <dd>{inspected.num_integer_variables}</dd>
            <dt>Equalities</dt>
            <dd>{inspected.num_equalities}</dd>
            <dt>Inequalities</dt>
            <dd>{inspected.num_inequalities}</dd>
            <dt>Fixed charge</dt>
            <dd>{ksh(inspected.fixed_charge)}</dd>
          </dl>
        </Panel>
      ) : null}

      {run ? <RunReport result={run} /> : null}
    </div>
  );
}

function RunReport({ result }: { result: EngineRunResult }) {
  const report = result.report;
  const econ = report.economics;
  const binding = report.binding_constraints.slice(0, 8);

  return (
    <TruthFrame kind="optimization-result">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <TruthClassLabel kind="optimization-result" />
        <Badge tone={result.solver_status === "OPTIMAL" ? "normal" : "warning"}>
          {result.solver_status}
        </Badge>
      </div>
      <h2 className="type-section mt-2">{result.contract_title}</h2>
      <dl className="io-readout mt-3">
        <dt>Solver</dt>
        <dd>{result.solver_name}</dd>
        <dt>Objective</dt>
        <dd>{result.objective_value !== null ? ksh(result.objective_value) : "—"}</dd>
        <dt>Solve time</dt>
        <dd>{formatNumber(result.solve_time_seconds, 3)} s</dd>
        <dt>Feasible</dt>
        <dd>{report.feasibility.is_verified_feasible ? "Verified" : "No"}</dd>
        <dt>Max violation</dt>
        <dd>{report.feasibility.max_violation.toExponential(2)}</dd>
      </dl>

      {report.infeasibility.is_infeasible ? (
        <ul className="mt-3 list-disc pl-5 type-body">
          {report.infeasibility.evidence_messages.map((message) => (
            <li key={message}>{message}</li>
          ))}
        </ul>
      ) : null}

      <h3 className="type-panel mt-4">Cost reconstruction</h3>
      <dl className="io-readout mt-2">
        <dt>Total</dt>
        <dd>{ksh(econ.total_cost)}</dd>
        <dt>Energy (variable)</dt>
        <dd>{ksh(econ.energy_variable)}</dd>
        <dt>Energy (fixed)</dt>
        <dd>{ksh(econ.energy_fixed)}</dd>
        <dt>Demand charge</dt>
        <dd>{ksh(econ.demand_charge)}</dd>
        <dt>Purchases</dt>
        <dd>{ksh(econ.purchase)}</dd>
        <dt>Setups</dt>
        <dd>{ksh(econ.startup)}</dd>
        <dt>Holding</dt>
        <dd>{ksh(econ.holding)}</dd>
        <dt>Facility</dt>
        <dd>{ksh(econ.fixed_charge)}</dd>
      </dl>

      <h3 className="type-panel mt-4">Machines</h3>
      <ul className="mt-2 flex flex-col gap-1">
        {Object.values(report.operations).map((machine) => (
          <li key={machine.machine_id} className="type-body">
            {machine.machine_id}: {formatNumber(machine.average_utilization * 100, 1)}% util ·{" "}
            {formatNumber(machine.operating_hours, 1)} h · {machine.total_startups} startups
          </li>
        ))}
      </ul>

      <h3 className="type-panel mt-4">Binding constraints</h3>
      <ul className="mt-2 flex flex-col gap-1">
        {binding.map((row) => (
          <li key={row.equation_id} className="type-meta text-secondary">
            [{row.category}] {row.equation_id} · {row.state} · LHS {formatNumber(row.lhs_value, 2)} /
            RHS {formatNumber(row.rhs_value, 2)}
          </li>
        ))}
      </ul>

      <h3 className="type-panel mt-4">Mass balance</h3>
      <ul className="mt-2 flex flex-col gap-1">
        {Object.values(report.resource_flows).map((flow) => (
          <li key={flow.resource_id} className="type-meta text-secondary">
            {flow.resource_id}: {formatNumber(flow.initial_stock, 1)} → {formatNumber(flow.final_stock, 1)}{" "}
            (residual {flow.conservation_residual.toExponential(1)})
          </li>
        ))}
      </ul>
    </TruthFrame>
  );
}
