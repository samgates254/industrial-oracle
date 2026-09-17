import { describe, expect, it } from "vitest";
import { plantTopologyDemo } from "./plant-topology";

describe("plant topology demo", () => {
  it("is explicitly demo-sourced", () => {
    expect(plantTopologyDemo.meta.source).toBe("demo");
    expect(plantTopologyDemo.meta.disclaimer).toMatch(/SYNTHETIC DEMO DATA/);
  });

  it("uses only named Command Center entities", () => {
    const names = plantTopologyDemo.nodes.map((node) => node.name);
    expect(names).toEqual(
      expect.arrayContaining([
        "Line 01",
        "Line 02 Assembly",
        "M-204",
        "Line 03",
        "BUF-L03",
        "Docks",
        "Electrical demand",
      ]),
    );
    expect(names).not.toContain("Area A");
  });

  it("does not invent economic impact", () => {
    expect(plantTopologyDemo.bottleneck?.economicImpactPerHour).toBeNull();
    expect(
      plantTopologyDemo.impact.some((item) => item.label === "Economic impact"),
    ).toBe(true);
  });

  it("marks Line 02 / M-204 as the binding constraint path", () => {
    const line02 = plantTopologyDemo.nodes.find((n) => n.id === "line_02");
    const edge = plantTopologyDemo.edges.find((e) => e.id === "e_l2_m204");
    expect(line02?.constraintLabel).toBe("M-204");
    expect(edge?.constrained).toBe(true);
  });
});
