import { describe, expect, it } from "vitest";
import {
  hierarchyMeta,
  informationHierarchy,
  plantOverviewContract,
  productionContract,
  truthClassMeta,
} from "./visual-architecture";

describe("information hierarchy", () => {
  it("locks plant state above KPI-style deep-dive", () => {
    expect(informationHierarchy[0]).toBe("plant-state");
    expect(informationHierarchy[2]).toBe("constraint");
    expect(informationHierarchy.indexOf("constraint")).toBeLessThan(
      informationHierarchy.indexOf("telemetry"),
    );
    expect(hierarchyMeta["plant-state"].level).toBe(1);
    expect(hierarchyMeta.constraint.level).toBe(3);
    expect(hierarchyMeta["deep-dive"].level).toBe(7);
  });
});

describe("truth classes", () => {
  it("keeps four mutually exclusive classes", () => {
    expect(Object.keys(truthClassMeta)).toEqual([
      "system-fact",
      "optimization-result",
      "ai-interpretation",
      "human-decision",
    ]);
  });

  it("does not reuse the AI surface for facts or solver output", () => {
    expect(truthClassMeta["system-fact"].surfaceClass).toBe("truth-fact");
    expect(truthClassMeta["optimization-result"].surfaceClass).toBe("truth-optimization");
    expect(truthClassMeta["ai-interpretation"].surfaceClass).toBe("truth-ai");
    expect(truthClassMeta["human-decision"].surfaceClass).toBe("truth-decision");
  });
});

describe("future screen contracts", () => {
  it("forbids a KPI-grid plant overview", () => {
    expect(plantOverviewContract.visual).toBe("process-topology");
    expect(plantOverviewContract.not).toBe("kpi-grid");
  });

  it("forbids ERP-CRUD production", () => {
    expect(productionContract.visual).toBe("deviation-locator");
    expect(productionContract.not).toBe("erp-crud");
  });
});
