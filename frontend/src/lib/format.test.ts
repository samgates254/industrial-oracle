import { describe, expect, it } from "vitest";
import { classifyFreshness, formatAge, formatSigned, moneyOrUnavailable } from "./format";

describe("formatSigned", () => {
  it("uses a minus sign for negatives", () => {
    expect(formatSigned(-0.8, 1, "pp")).toBe("−0.8 pp");
  });
});

describe("classifyFreshness", () => {
  const now = "2026-09-16T14:32:08.000Z";

  it("returns live within 15s", () => {
    expect(classifyFreshness("2026-09-16T14:32:00.000Z", now)).toBe("live");
  });

  it("returns stale after 2 minutes", () => {
    expect(classifyFreshness("2026-09-16T14:29:00.000Z", now)).toBe("stale");
  });
});

describe("formatAge", () => {
  it("formats minute-second age", () => {
    expect(formatAge("2026-09-16T14:29:54.000Z", "2026-09-16T14:32:08.000Z")).toBe(
      "2m 14s",
    );
  });
});

describe("moneyOrUnavailable", () => {
  it("does not invent an economic value", () => {
    expect(moneyOrUnavailable(null, "not computed")).toBe("not computed");
  });
});
