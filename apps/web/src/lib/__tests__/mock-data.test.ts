/**
 * Smoke tests for mock data fixtures — validates structure and integrity.
 */
import { describe, it, expect } from "vitest";
import {
  mockProfile,
  mockParsedJD,
  mockGeneratedBullets,
  mockValidationReport,
  mockDiffBullets,
} from "../mock-data";

describe("mockProfile", () => {
  it("has required top-level fields", () => {
    expect(mockProfile.profile_id).toBeDefined();
    expect(mockProfile.version).toBeDefined();
    expect(mockProfile.owner.full_name).toBeDefined();
  });

  it("has at least one approved experience", () => {
    const approved = mockProfile.experiences.filter((e) => e.approved);
    expect(approved.length).toBeGreaterThan(0);
  });

  it("has at least one approved education entry", () => {
    const approved = mockProfile.education.filter((e) => e.approved);
    expect(approved.length).toBeGreaterThan(0);
  });

  it("has skills defined", () => {
    expect(mockProfile.skills.length).toBeGreaterThan(0);
  });

  it("has bullets on experiences", () => {
    const hasBullets = mockProfile.experiences.some((e) => e.bullets.length > 0);
    expect(hasBullets).toBe(true);
  });
});

describe("mockParsedJD", () => {
  it("has required skills", () => {
    expect(mockParsedJD.required_skills.length).toBeGreaterThan(0);
  });

  it("has job_id", () => {
    expect(mockParsedJD.job_id).toBeDefined();
  });

  it("has role signals", () => {
    expect(mockParsedJD.role_signals).toBeDefined();
    expect(typeof mockParsedJD.role_signals.backend).toBe("number");
  });
});

describe("mockGeneratedBullets", () => {
  it("contains bullets with text", () => {
    expect(mockGeneratedBullets.length).toBeGreaterThan(0);
    for (const b of mockGeneratedBullets) {
      expect(b.id).toBeDefined();
      expect(b.text.length).toBeGreaterThan(0);
    }
  });
});

describe("mockValidationReport", () => {
  it("has a status and summary", () => {
    expect(mockValidationReport.status).toBeDefined();
    expect(mockValidationReport.summary).toBeDefined();
  });

  it("summary has numeric values", () => {
    const { summary } = mockValidationReport;
    expect(typeof summary.supported_claims).toBe("number");
    expect(typeof summary.rejected_claims).toBe("number");
  });
});

describe("mockDiffBullets", () => {
  it("has diff bullets with original and generated text", () => {
    expect(mockDiffBullets.length).toBeGreaterThan(0);
    for (const d of mockDiffBullets) {
      expect(d.original).toBeDefined();
      expect(d.generated).toBeDefined();
    }
  });
});
