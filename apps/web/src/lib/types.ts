// TypeScript types mirroring Pydantic schemas in packages/core/src/tailortex/schemas/

export interface Link {
  label: string;
  url: string;
}

export interface Owner {
  full_name: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  links: Link[];
}

export interface SourceRef {
  document_id: string;
  line_range: [number, number] | null;
}

export interface Bullet {
  id: string;
  text: string;
  skills: string[];
  metrics: string[];
  evidence_ids: string[];
  approved: boolean;
}

export interface Experience {
  id: string;
  organization: string;
  title: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  source: {
    type: string;
    path: string | null;
    line_range: [number, number] | null;
  } | null;
  approved: boolean;
  bullets: Bullet[];
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  url: string | null;
  skills: string[];
  bullets: Bullet[];
  approved: boolean;
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  field: string | null;
  start_date: string | null;
  end_date: string | null;
  gpa: string | null;
  approved: boolean;
}

export interface Skill {
  name: string;
  category: string | null;
  proficiency: string | null;
  evidence_ids: string[];
  approved: boolean;
}

export interface EvidenceLedgerEntry {
  id: string;
  claim_type: string;
  source_text: string;
  normalized_claim: string;
  source_ref: SourceRef | null;
  allowed_transformations: string[];
  blocked_transformations: string[];
  requires_user_confirmation: boolean;
}

export interface Summary {
  source_text: string;
  approved: boolean;
}

export interface CanonicalProfile {
  profile_id: string;
  version: string;
  owner: Owner;
  summary: Summary | null;
  experiences: Experience[];
  projects: Project[];
  education: Education[];
  skills: Skill[];
  certifications: string[];
  publications: string[];
  awards: string[];
  evidence_ledger: EvidenceLedgerEntry[];
  created_at: string;
  updated_at: string;
}

export interface RoleSignals {
  backend: number;
  frontend: number;
  machine_learning: number;
  qa: number;
  leadership: number;
  [key: string]: number;
}

export interface ParsedJobDescription {
  job_id: string;
  source: { type: string; url: string | null };
  company: string | null;
  role_title: string | null;
  location: string | null;
  employment_type: string | null;
  seniority: string | null;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  domain_keywords: string[];
  role_signals: RoleSignals;
  prompt_injection_flags: string[];
  created_at: string;
}

export interface KeywordStrategy {
  covered: string[];
  not_covered: string[];
  do_not_insert: Array<{ keyword: string; reason: string }>;
}

export interface SectionPlan {
  type: string;
  source_ids: string[];
  selected_bullet_ids: string[];
  reason: string;
}

export interface ResumePlan {
  resume_id: string;
  target_job_id: string;
  template_id: string;
  sections: SectionPlan[];
  keyword_strategy: KeywordStrategy;
}

export interface GeneratedBullet {
  id: string;
  text: string;
  source_bullet_ids: string[];
  evidence_ids: string[];
  jd_keywords_used: string[];
  validation_status: "supported" | "needs_confirmation" | "rejected";
  validation_notes: string[];
}

export interface ClaimResult {
  claim: string;
  status: "supported" | "needs_confirmation" | "rejected";
  evidence_ids: string[];
}

export interface ValidationWarning {
  type: string;
  message: string;
}

export interface ValidationReport {
  resume_id: string;
  status: "passed" | "passed_with_warnings" | "failed";
  summary: {
    supported_claims: number;
    needs_confirmation: number;
    rejected_claims: number;
    latex_errors: number;
    warnings: number;
  };
  claims: ClaimResult[];
  warnings: ValidationWarning[];
}

export interface TailoringOptions {
  mode: "conservative" | "impact_focused" | "technical_depth" | "research_focused";
  target_role_family: string;
  max_pages: number;
  allow_bold_keywords: boolean;
  allow_summary: boolean;
  llm_provider: string;
  redaction_enabled: boolean;
  require_user_confirmation_for_metrics: boolean;
}
