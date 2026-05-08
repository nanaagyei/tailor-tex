import type {
  CanonicalProfile,
  ParsedJobDescription,
  ValidationReport,
  GeneratedBullet,
} from "./types";

export interface DiffBullet {
  id: string;
  original: string;
  generated: string;
  validation_status: "supported" | "needs_confirmation" | "rejected";
  changes: Array<{ type: "added" | "removed" | "unchanged"; text: string }>;
}

export const mockDiffBullets: DiffBullet[] = [
  {
    id: "diff_001",
    original:
      "Designed and maintained CI/CD pipelines using GitHub Actions, reducing deploy time by 40%.",
    generated:
      "Architected and maintained CI/CD pipelines with GitHub Actions, cutting deployment cycle time by 40% across the engineering team.",
    validation_status: "supported",
    changes: [
      { type: "removed", text: "Designed" },
      { type: "added", text: "Architected" },
      { type: "unchanged", text: " and maintained CI/CD pipelines " },
      { type: "removed", text: "using" },
      { type: "added", text: "with" },
      { type: "unchanged", text: " GitHub Actions, " },
      { type: "removed", text: "reducing deploy time" },
      { type: "added", text: "cutting deployment cycle time" },
      { type: "unchanged", text: " by 40%" },
      { type: "added", text: " across the engineering team" },
      { type: "unchanged", text: "." },
    ],
  },
  {
    id: "diff_002",
    original:
      "Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day.",
    generated:
      "Developed and scaled REST API services in Python using FastAPI, handling over 2 million daily requests with 99.9% uptime.",
    validation_status: "supported",
    changes: [
      { type: "removed", text: "Built" },
      { type: "added", text: "Developed and scaled" },
      { type: "unchanged", text: " REST API " },
      { type: "removed", text: "endpoints" },
      { type: "added", text: "services" },
      { type: "unchanged", text: " in Python " },
      { type: "removed", text: "(FastAPI) serving 2M+ requests/day" },
      {
        type: "added",
        text: "using FastAPI, handling over 2 million daily requests with 99.9% uptime",
      },
      { type: "unchanged", text: "." },
    ],
  },
  {
    id: "diff_003",
    original:
      "Implemented structured logging and tracing with OpenTelemetry across 12 microservices.",
    generated:
      "Deployed structured observability across 12 microservices using OpenTelemetry, enabling faster incident triage and resolution.",
    validation_status: "needs_confirmation",
    changes: [
      { type: "removed", text: "Implemented structured logging and tracing with OpenTelemetry" },
      { type: "added", text: "Deployed structured observability" },
      { type: "unchanged", text: " across 12 microservices" },
      { type: "removed", text: "." },
      {
        type: "added",
        text: " using OpenTelemetry, enabling faster incident triage and resolution.",
      },
    ],
  },
];

export const mockProfile: CanonicalProfile = {
  profile_id: "default",
  version: "1.0.0",
  owner: {
    full_name: "Morgan Castillo",
    email: "morgan.castillo@proton.me",
    phone: null,
    location: "Austin, TX",
    links: [
      { label: "GitHub", url: "https://github.com/mcastillo-dev" },
      { label: "LinkedIn", url: "https://linkedin.com/in/mcastillo" },
    ],
  },
  summary: {
    source_text:
      "Software engineer with 4 years of experience building backend services, testing infrastructure, and developer tooling. Focused on Python, Go, and cloud-native architectures.",
    approved: true,
  },
  experiences: [
    {
      id: "exp_meridian_swe",
      organization: "Meridian Systems",
      title: "Software Engineer",
      location: "Austin, TX",
      start_date: "2023-03",
      end_date: null,
      is_current: true,
      source: { type: "resume_import", path: null, line_range: [12, 28] },
      approved: true,
      bullets: [
        {
          id: "bullet_001",
          text: "Designed and maintained CI/CD pipelines using GitHub Actions, reducing deploy time by 40%.",
          skills: ["CI/CD", "GitHub Actions"],
          metrics: ["40% reduction in deploy time"],
          evidence_ids: ["ev_001"],
          approved: true,
        },
        {
          id: "bullet_002",
          text: "Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day.",
          skills: ["Python", "FastAPI", "REST APIs"],
          metrics: ["2M+ requests/day"],
          evidence_ids: ["ev_002"],
          approved: true,
        },
        {
          id: "bullet_003",
          text: "Implemented structured logging and tracing with OpenTelemetry across 12 microservices.",
          skills: ["OpenTelemetry", "observability", "microservices"],
          metrics: [],
          evidence_ids: ["ev_003"],
          approved: true,
        },
      ],
    },
    {
      id: "exp_tidewater_qa",
      organization: "Tidewater Analytics",
      title: "QA Engineer",
      location: "Remote",
      start_date: "2021-06",
      end_date: "2023-02",
      is_current: false,
      source: { type: "resume_import", path: null, line_range: [30, 44] },
      approved: true,
      bullets: [
        {
          id: "bullet_004",
          text: "Developed automated test suites using Pytest and Selenium, covering 85% of critical user paths.",
          skills: ["Pytest", "Selenium", "test automation"],
          metrics: ["85% coverage of critical paths"],
          evidence_ids: ["ev_004"],
          approved: true,
        },
        {
          id: "bullet_005",
          text: "Reduced production bug escape rate by 30% through integration testing improvements.",
          skills: ["integration testing", "QA"],
          metrics: ["30% reduction in bug escape rate"],
          evidence_ids: ["ev_005"],
          approved: true,
        },
      ],
    },
  ],
  projects: [
    {
      id: "proj_logpipe",
      name: "LogPipe",
      description: "Open-source log aggregation CLI tool for local development.",
      url: "https://github.com/mcastillo-dev/logpipe",
      skills: ["Go", "CLI", "logging"],
      bullets: [
        {
          id: "bullet_006",
          text: "Built a Go CLI tool that aggregates logs from multiple Docker containers into a unified stream.",
          skills: ["Go", "Docker", "CLI"],
          metrics: [],
          evidence_ids: ["ev_006"],
          approved: true,
        },
      ],
      approved: true,
    },
  ],
  education: [
    {
      id: "edu_utexas",
      institution: "University of Texas at Austin",
      degree: "B.S.",
      field: "Computer Science",
      start_date: "2017-08",
      end_date: "2021-05",
      gpa: "3.7",
      approved: true,
    },
  ],
  skills: [
    { name: "Python", category: "Languages", proficiency: "advanced", evidence_ids: ["ev_002", "ev_004"], approved: true },
    { name: "Go", category: "Languages", proficiency: "intermediate", evidence_ids: ["ev_006"], approved: true },
    { name: "FastAPI", category: "Frameworks", proficiency: "advanced", evidence_ids: ["ev_002"], approved: true },
    { name: "Docker", category: "Tools", proficiency: "intermediate", evidence_ids: ["ev_006"], approved: true },
    { name: "GitHub Actions", category: "Tools", proficiency: "advanced", evidence_ids: ["ev_001"], approved: true },
    { name: "PostgreSQL", category: "Databases", proficiency: "intermediate", evidence_ids: [], approved: true },
    { name: "REST APIs", category: "Concepts", proficiency: "advanced", evidence_ids: ["ev_002"], approved: true },
    { name: "Pytest", category: "Testing", proficiency: "advanced", evidence_ids: ["ev_004"], approved: true },
  ],
  certifications: [],
  publications: [],
  awards: [],
  evidence_ledger: [
    {
      id: "ev_001",
      claim_type: "experience",
      source_text: "Designed and maintained CI/CD pipelines using GitHub Actions, reducing deploy time by 40%.",
      normalized_claim: "Maintained CI/CD pipelines with GitHub Actions.",
      source_ref: { document_id: "source_resume", line_range: [14, 15] },
      allowed_transformations: ["tighten wording", "map wording to JD terminology"],
      blocked_transformations: ["invent metrics", "add tools not present"],
      requires_user_confirmation: false,
    },
    {
      id: "ev_002",
      claim_type: "experience",
      source_text: "Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day.",
      normalized_claim: "Built REST APIs with FastAPI handling high traffic.",
      source_ref: { document_id: "source_resume", line_range: [16, 17] },
      allowed_transformations: ["tighten wording", "map wording to JD terminology"],
      blocked_transformations: ["invent metrics", "add tools not present"],
      requires_user_confirmation: false,
    },
  ],
  created_at: "2025-05-01T10:00:00Z",
  updated_at: "2025-05-04T14:30:00Z",
};

export const mockParsedJD: ParsedJobDescription = {
  job_id: "meridian-backend-swe-2025",
  source: { type: "pasted_text", url: null },
  company: "Apex Engineering",
  role_title: "Backend Software Engineer",
  location: "Remote (US)",
  employment_type: "Full-time",
  seniority: "mid",
  required_skills: ["Python", "REST APIs", "SQL", "Docker", "CI/CD"],
  preferred_skills: ["Go", "Kubernetes", "AWS", "gRPC"],
  responsibilities: [
    "Design and build scalable backend services",
    "Write and maintain comprehensive test suites",
    "Collaborate with cross-functional product teams",
    "Participate in on-call rotation and incident response",
  ],
  domain_keywords: ["backend", "microservices", "distributed systems"],
  role_signals: {
    backend: 0.9,
    frontend: 0.05,
    machine_learning: 0.0,
    qa: 0.15,
    leadership: 0.2,
  },
  prompt_injection_flags: [],
  created_at: "2025-05-04T15:00:00Z",
};

export const mockGeneratedBullets: GeneratedBullet[] = [
  {
    id: "gen_001",
    text: "Architected and maintained CI/CD pipelines with GitHub Actions, cutting deployment cycle time by 40% across the engineering team.",
    source_bullet_ids: ["bullet_001"],
    evidence_ids: ["ev_001"],
    jd_keywords_used: ["CI/CD"],
    validation_status: "supported",
    validation_notes: [],
  },
  {
    id: "gen_002",
    text: "Developed and scaled REST API services in Python using FastAPI, handling over 2 million daily requests with 99.9% uptime.",
    source_bullet_ids: ["bullet_002"],
    evidence_ids: ["ev_002"],
    jd_keywords_used: ["Python", "REST APIs"],
    validation_status: "supported",
    validation_notes: [],
  },
  {
    id: "gen_003",
    text: "Deployed structured observability across 12 microservices using OpenTelemetry, enabling faster incident triage and resolution.",
    source_bullet_ids: ["bullet_003"],
    evidence_ids: ["ev_003"],
    jd_keywords_used: ["microservices"],
    validation_status: "needs_confirmation",
    validation_notes: ["Metric 'faster incident triage' not directly sourced from resume."],
  },
];

export const mockValidationReport: ValidationReport = {
  resume_id: "resume_apex_backend_swe",
  status: "passed_with_warnings",
  summary: {
    supported_claims: 5,
    needs_confirmation: 1,
    rejected_claims: 0,
    latex_errors: 0,
    warnings: 2,
  },
  claims: [
    { claim: "CI/CD pipelines with GitHub Actions, 40% deploy time reduction", status: "supported", evidence_ids: ["ev_001"] },
    { claim: "REST API services in Python using FastAPI, 2M+ daily requests", status: "supported", evidence_ids: ["ev_002"] },
    { claim: "Observability across 12 microservices", status: "supported", evidence_ids: ["ev_003"] },
    { claim: "Automated test suites, 85% critical path coverage", status: "supported", evidence_ids: ["ev_004"] },
    { claim: "30% reduction in bug escape rate", status: "supported", evidence_ids: ["ev_005"] },
    { claim: "Faster incident triage and resolution", status: "needs_confirmation", evidence_ids: ["ev_003"] },
  ],
  warnings: [
    { type: "missing_keyword", message: "JD mentions Kubernetes, but no approved Kubernetes evidence exists in the profile." },
    { type: "missing_keyword", message: "JD mentions AWS, but no approved AWS evidence exists in the profile." },
  ],
};
