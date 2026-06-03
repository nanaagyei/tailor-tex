/**
 * Tests for the API client — fetch calls are mocked via global fetch.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  checkHealth,
  listProfiles,
  getProfile,
  saveProfile,
  deleteProfile,
  parseJD,
  listApplications,
  getApplication,
  deleteApplication,
  tailorResume,
  renderResume,
  getConfig,
  updateConfig,
} from "../api";

function mockFetch(status: number, data: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("checkHealth", () => {
  it("returns health data on success", async () => {
    globalThis.fetch = mockFetch(200, { status: "ok", version: "0.1.0" });
    const result = await checkHealth();
    expect(result.status).toBe("ok");
    expect(result.version).toBe("0.1.0");
  });

  it("throws ApiError on failure", async () => {
    globalThis.fetch = mockFetch(500, { error: "down" });
    await expect(checkHealth()).rejects.toThrow();
  });
});

describe("listProfiles", () => {
  it("returns profile IDs", async () => {
    globalThis.fetch = mockFetch(200, ["default", "morgan"]);
    const result = await listProfiles();
    expect(result).toEqual(["default", "morgan"]);
  });
});

describe("getProfile", () => {
  it("fetches a profile by ID", async () => {
    const profile = { profile_id: "test", version: "1.0.0", owner: { full_name: "Test" } };
    globalThis.fetch = mockFetch(200, profile);
    const result = await getProfile("test");
    expect(result.profile_id).toBe("test");
  });
});

describe("saveProfile", () => {
  it("saves a profile and returns status", async () => {
    globalThis.fetch = mockFetch(200, { status: "saved", profile_id: "p1" });
    // @ts-expect-error — partial profile for test
    const result = await saveProfile({ profile_id: "p1", version: "1.0.0", owner: { full_name: "X" } });
    expect(result.status).toBe("saved");
  });
});

describe("deleteProfile", () => {
  it("deletes a profile by ID", async () => {
    globalThis.fetch = mockFetch(200, { status: "deleted" });
    const result = await deleteProfile("p1");
    expect(result.status).toBe("deleted");
  });
});

describe("parseJD", () => {
  it("parses JD text and returns structured data", async () => {
    const jd = {
      job_id: "jd-1",
      source: { type: "pasted_text" },
      required_skills: ["Python"],
      preferred_skills: [],
      responsibilities: ["Build APIs"],
      role_signals: { backend: 0.5, frontend: 0, machine_learning: 0, qa: 0, leadership: 0 },
      prompt_injection_flags: [],
    };
    globalThis.fetch = mockFetch(200, jd);
    const result = await parseJD("We need Python devs");
    expect(result.job_id).toBe("jd-1");
    expect(result.required_skills).toContain("Python");
  });
});

describe("listApplications", () => {
  it("returns application IDs", async () => {
    globalThis.fetch = mockFetch(200, ["app-1", "app-2"]);
    const result = await listApplications();
    expect(result).toEqual(["app-1", "app-2"]);
  });
});

describe("getApplication", () => {
  it("fetches application data", async () => {
    globalThis.fetch = mockFetch(200, { app_id: "app-1", data: {} });
    const result = await getApplication("app-1");
    expect(result.app_id).toBe("app-1");
  });
});

describe("deleteApplication", () => {
  it("deletes an application", async () => {
    globalThis.fetch = mockFetch(200, { status: "deleted" });
    const result = await deleteApplication("app-1");
    expect(result.status).toBe("deleted");
  });
});

describe("tailorResume", () => {
  it("calls the tailor endpoint with correct params", async () => {
    const response = {
      plan: { resume_id: "r-1", target_job_id: "jd-1", template_id: "ats-modern", sections: [] },
      generated_bullets: [],
      validation: {
        resume_id: "r-1",
        status: "passed",
        summary: { supported_claims: 0, needs_confirmation: 0, rejected_claims: 0, warnings: 0 },
        claims: [],
        warnings: [],
      },
    };
    globalThis.fetch = mockFetch(200, response);
    const result = await tailorResume({ jd_id: "jd-1" });
    expect(result.plan.resume_id).toBe("r-1");
    expect(result.validation.status).toBe("passed");
  });
});

describe("renderResume", () => {
  it("returns rendered tex", async () => {
    globalThis.fetch = mockFetch(200, { tex: "\\documentclass{article}" });
    const result = await renderResume({ jd_id: "jd-1" });
    expect(result.tex).toContain("\\documentclass");
  });
});

describe("getConfig", () => {
  it("returns workspace config", async () => {
    globalThis.fetch = mockFetch(200, { version: "1.0.0", provider: "ollama" });
    const result = await getConfig();
    expect(result.version).toBe("1.0.0");
  });
});

describe("updateConfig", () => {
  it("updates config and returns status", async () => {
    globalThis.fetch = mockFetch(200, { status: "saved" });
    const result = await updateConfig({ provider: "ollama" });
    expect(result.status).toBe("saved");
  });
});
