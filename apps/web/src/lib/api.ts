/**
 * API client for the TailorTex FastAPI backend.
 *
 * All calls go to localhost:7745 (the local API server).
 */

import type {
  CanonicalProfile,
  GeneratedBullet,
  ParsedJobDescription,
  ResumePlan,
  ValidationReport,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7745";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, body);
  }

  return res.json() as Promise<T>;
}

// ── Health ──────────────────────────────────────────────

export async function checkHealth(): Promise<{
  status: string;
  version: string;
}> {
  return request("/health");
}

// ── Profiles ────────────────────────────────────────────

export async function listProfiles(): Promise<string[]> {
  return request("/profiles");
}

export async function getProfile(
  profileId: string,
): Promise<CanonicalProfile> {
  return request(`/profiles/${encodeURIComponent(profileId)}`);
}

export async function saveProfile(
  profile: CanonicalProfile,
): Promise<{ status: string; profile_id: string }> {
  return request("/profiles", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

export async function deleteProfile(
  profileId: string,
): Promise<{ status: string }> {
  return request(`/profiles/${encodeURIComponent(profileId)}`, {
    method: "DELETE",
  });
}

// ── Import ──────────────────────────────────────────────

export async function importResume(
  file: File,
): Promise<{ status: string; draft: Record<string, unknown>; warnings: string[] }> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE}/import`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "Upload failed");
    throw new ApiError(res.status, body);
  }

  return res.json();
}

// ── JD Parsing ──────────────────────────────────────────

export async function parseJD(
  text: string,
  company?: string,
  roleTitle?: string,
): Promise<ParsedJobDescription> {
  return request("/jd/parse", {
    method: "POST",
    body: JSON.stringify({
      text,
      company: company ?? null,
      role_title: roleTitle ?? null,
    }),
  });
}

// ── Applications ────────────────────────────────────────

export async function listApplications(): Promise<string[]> {
  return request("/applications");
}

export async function getApplication(
  appId: string,
): Promise<Record<string, unknown>> {
  return request(`/applications/${encodeURIComponent(appId)}`);
}

export async function deleteApplication(
  appId: string,
): Promise<{ status: string }> {
  return request(`/applications/${encodeURIComponent(appId)}`, {
    method: "DELETE",
  });
}

// ── Tailoring ───────────────────────────────────────────

export interface TailorResult {
  plan: ResumePlan;
  generated_bullets: GeneratedBullet[];
  validation: ValidationReport;
}

export async function tailorResume(params: {
  profile_id?: string;
  jd_id: string;
  mode?: string;
  template_id?: string;
}): Promise<TailorResult> {
  return request("/tailor", {
    method: "POST",
    body: JSON.stringify({
      profile_id: params.profile_id ?? "default",
      jd_id: params.jd_id,
      mode: params.mode ?? "conservative",
      template_id: params.template_id ?? "ats-modern",
    }),
  });
}

// ── Rendering ───────────────────────────────────────────

export async function renderResume(params: {
  profile_id?: string;
  jd_id: string;
  template_id?: string;
}): Promise<{ tex: string }> {
  return request("/render", {
    method: "POST",
    body: JSON.stringify({
      profile_id: params.profile_id ?? "default",
      jd_id: params.jd_id,
      template_id: params.template_id ?? "ats-modern",
    }),
  });
}

// ── Config ──────────────────────────────────────────────

export async function getConfig(): Promise<Record<string, unknown>> {
  return request("/config");
}

export async function updateConfig(
  config: Record<string, unknown>,
): Promise<{ status: string }> {
  return request("/config", {
    method: "PUT",
    body: JSON.stringify(config),
  });
}
