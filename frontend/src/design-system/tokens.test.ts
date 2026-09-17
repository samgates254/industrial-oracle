import { describe, expect, it } from "vitest";
import { evidenceKinds, systemStates, tokenCategories } from "./tokens";

describe("design tokens", () => {
  it("covers required semantic categories", () => {
    expect(tokenCategories).toEqual(
      expect.arrayContaining([
        "background",
        "border",
        "text",
        "system-state",
        "industrial-data",
        "intelligence",
        "audit",
        "truth-class",
        "information-hierarchy",
        "spacing",
        "typography",
        "radius",
        "motion",
      ]),
    );
  });

  it("separates evidence kinds", () => {
    expect(evidenceKinds).toEqual([
      "system-fact",
      "optimization-result",
      "ai-interpretation",
      "human-decision",
    ]);
  });

  it("includes operational states", () => {
    expect(systemStates).toContain("critical");
    expect(systemStates).toContain("warning");
    expect(systemStates).toContain("offline");
  });
});
