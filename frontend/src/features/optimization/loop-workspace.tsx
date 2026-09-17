"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel, SectionHeader } from "@/components/ui/panel";
import { ApiError } from "@/lib/api/client";
import {
  authorizeDecision,
  executeDecision,
  runSyntheticSimulation,
  backendFetch,
} from "@/lib/api/backend";

type Overview = {
  operational_state: {
    actual_throughput: number | null;
    target_throughput: number | null;
    bottleneck_asset_id: string | null;
    total_events_processed: number;
  };
  active_constraints: { constraint_id: string; entity_id: string; observed_value: number; required_value: number | null }[];
  pending_decisions: { decision_id: string; title: string; status: string }[];
  m816_optimization: { solver_status: string | null; solver_name: string | null; objective_value: number | null };
};

export function LoopWorkspace() {
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<string>("");
  const [overview, setOverview] = useState<Overview | null>(null);

  async function refresh() {
    const data = await backendFetch<Overview>("/api/v1/intelligence/command-center/overview?plant_id=P-01");
    setOverview(data);
    return data;
  }

  async function ingest() {
    setBusy("ingest");
    try {
      const sim = await runSyntheticSimulation("P-01");
      const ov = await refresh();
      setLog(
        `Simulation ${String(sim.status)}. Events processed=${ov.operational_state.total_events_processed}. Bottleneck=${ov.operational_state.bottleneck_asset_id}. Solver=${ov.m816_optimization.solver_status}.`,
      );
    } catch (error) {
      setLog(error instanceof ApiError ? error.message : "Ingest failed");
    } finally {
      setBusy(null);
    }
  }

  async function approveExecute() {
    setBusy("exec");
    try {
      const ov = overview ?? (await refresh());
      const dec = ov.pending_decisions[0];
      if (!dec) {
        setLog("No pending decision. Ingest synthetic events first.");
        return;
      }
      await authorizeDecision(dec.decision_id, true);
      const exec = await executeDecision(dec.decision_id);
      const after = await refresh();
      setLog(
        `Authorized ${dec.decision_id}. Execute ${JSON.stringify(exec)}. After: bottleneck=${after.operational_state.bottleneck_asset_id} throughput=${after.operational_state.actual_throughput}.`,
      );
    } catch (error) {
      setLog(error instanceof ApiError ? error.message : "Authorization/execution failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Panel>
      <SectionHeader
        eyebrow="Closed loop"
        title="Synthetic events → state → constraint → M8.16 → decision"
      />
      <p className="type-meta text-muted">
        This is the ZIP backend path. Data is SYNTHETIC, not live plant telemetry.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button size="sm" variant="optimize" disabled={busy !== null} onClick={() => void ingest()}>
          {busy === "ingest" ? "Ingesting…" : "Run synthetic plant"}
        </Button>
        <Button size="sm" disabled={busy !== null} onClick={() => void approveExecute()}>
          {busy === "exec" ? "Executing…" : "Approve + simulated execute"}
        </Button>
        <Button size="sm" disabled={busy !== null} onClick={() => void refresh().then(() => setLog("Refreshed overview"))}>
          Refresh state
        </Button>
      </div>
      {overview ? (
        <dl className="io-readout mt-3">
          <dt>Events</dt>
          <dd>{overview.operational_state.total_events_processed}</dd>
          <dt>Throughput</dt>
          <dd>
            {overview.operational_state.actual_throughput ?? "unavailable"} /{" "}
            {overview.operational_state.target_throughput ?? "unavailable"} pcs/h
          </dd>
          <dt>Bottleneck</dt>
          <dd>{overview.operational_state.bottleneck_asset_id ?? "none"}</dd>
          <dt>Constraints</dt>
          <dd>{overview.active_constraints.length}</dd>
          <dt>Solver</dt>
          <dd>
            {overview.m816_optimization.solver_name ?? "—"} {overview.m816_optimization.solver_status ?? "NOT_RUN"}
          </dd>
          <dt>Decision</dt>
          <dd>{overview.pending_decisions[0]?.decision_id ?? "none"}</dd>
        </dl>
      ) : (
        <p className="type-body mt-3 text-secondary">No backend snapshot loaded.</p>
      )}
      {log ? <p className="type-meta mt-3 text-secondary">{log}</p> : null}
      <Badge tone="demo" className="mt-3">
        SYNTHETIC
      </Badge>
    </Panel>
  );
}
