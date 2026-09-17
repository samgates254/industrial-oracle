import { describe, expect, it } from "vitest";
import { commandCenterDemo, DEMO_DISCLAIMER } from "./command-center";

describe("command center demo snapshot", () => {
  it("is explicitly demo-sourced", () => {
    expect(commandCenterDemo.meta.source).toBe("demo");
    expect(commandCenterDemo.meta.disclaimer).toBe(DEMO_DISCLAIMER);
  });

  it("does not invent economic bottleneck impact", () => {
    expect(commandCenterDemo.bottleneck?.economicImpactPerHour).toBeNull();
  });

  it("keeps AI distinct from solver output", () => {
    const kinds = commandCenterDemo.intelligence.map((b) => b.kind);
    expect(kinds).toContain("system-fact");
    expect(kinds).toContain("optimization-result");
    expect(kinds).toContain("ai-interpretation");
    expect(kinds).toContain("human-decision");
  });

  it("uses a deterministic snapshot clock", () => {
    expect(commandCenterDemo.meta.snapshotAt).toBe("2026-09-16T14:32:08+03:00");
  });
});
