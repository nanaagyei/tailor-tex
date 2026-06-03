/**
 * Tests for the cn() utility — clsx + tailwind-merge wrapper.
 */
import { describe, it, expect } from "vitest";
import { cn } from "../utils";

describe("cn", () => {
  it("returns an empty string when called with no arguments", () => {
    expect(cn()).toBe("");
  });

  it("combines string class names with spaces", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("filters out falsy values", () => {
    expect(cn("foo", false, undefined, null, "bar")).toBe("foo bar");
  });

  it("handles conditional object syntax", () => {
    expect(cn("base", { active: true, disabled: false })).toBe("base active");
  });

  it("merges tailwind utilities (last wins)", () => {
    expect(cn("px-4", "px-2")).toBe("px-2");
  });

  it("handles arrays of class values", () => {
    expect(cn(["foo", "bar"], "baz")).toBe("foo bar baz");
  });

  it("merges conflicting tailwind classes across multiple args", () => {
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });
});
