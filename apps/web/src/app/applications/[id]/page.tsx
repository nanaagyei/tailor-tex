"use client";

import { useState, useEffect, use, useCallback } from "react";
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  Eye,
  AlertTriangle,
  Loader2,
  ArrowRight,
  Zap,
  FileText,
  Target,
  Shield,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";
import { ValidationBadge } from "@/components/validation-badge";
import {
  getApplication,
  listProfiles,
  getProfile,
  tailorResume,
} from "@/lib/api";
import type {
  CanonicalProfile,
  ParsedJobDescription,
  GeneratedBullet,
  ValidationReport,
  ResumePlan,
} from "@/lib/types";

const MODES = [
  {
    value: "conservative",
    label: "Conservative",
    description: "Minimal rewrites, closest to original",
  },
  {
    value: "impact_focused",
    label: "Impact-Focused",
    description: "Emphasize metrics and outcomes",
  },
  {
    value: "technical_depth",
    label: "Technical Depth",
    description: "Highlight technical skills and architecture",
  },
  {
    value: "research_focused",
    label: "Research",
    description: "Academic and research emphasis",
  },
];

export default function TailoringWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [rewriteMode, setRewriteMode] = useState("conservative");
  const [profile, setProfile] = useState<CanonicalProfile | null>(null);
  const [jd, setJd] = useState<ParsedJobDescription | null>(null);
  const [bullets, setBullets] = useState<GeneratedBullet[]>([]);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [plan, setPlan] = useState<ResumePlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [tailoring, setTailoring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [appData, profiles] = await Promise.all([
          getApplication(id),
          listProfiles(),
        ]);

        const parsedJd = appData as unknown as ParsedJobDescription;
        setJd(parsedJd);

        if (profiles.length > 0) {
          const p = await getProfile(profiles[0]);
          setProfile(p);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load application."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleTailor = useCallback(async () => {
    if (!jd) return;
    setTailoring(true);
    setError(null);
    try {
      const result = await tailorResume({
        jd_id: id,
        profile_id: profile?.profile_id,
        mode: rewriteMode,
      });
      setPlan(result.plan);
      setBullets(result.generated_bullets);
      setReport(result.validation);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Tailoring failed."
      );
    } finally {
      setTailoring(false);
    }
  }, [jd, id, profile, rewriteMode]);

  // Auto-tailor on load
  useEffect(() => {
    if (jd && profile && bullets.length === 0 && !tailoring) {
      const timer = window.setTimeout(() => {
        void handleTailor();
      }, 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [jd, profile, bullets.length, tailoring, handleTailor]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex flex-col gap-4">
          <Skeleton className="h-8 w-64" />
          <div className="grid gap-4 lg:grid-cols-3">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error && !jd) {
    return (
      <AppShell>
        <EmptyState
          title="Application not found"
          description={error}
          action={{ label: "Parse a JD", href: "/jobs/new" }}
        />
      </AppShell>
    );
  }

  const currentMode = MODES.find((m) => m.value === rewriteMode);

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-col gap-4 mb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex size-10 items-center justify-center rounded-lg bg-emerald/10 ring-1 ring-emerald/20 shrink-0 mt-0.5">
            <Target className="size-4 text-emerald" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Tailoring Workspace
            </h1>
            <p className="text-sm text-muted-foreground">
              {jd?.role_title} at {jd?.company}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            render={<a href={`/applications/${id}/diff`} />}
          >
            <Eye className="size-4" data-icon="inline-start" />
            View Diff
          </Button>
          <Button size="sm" render={<a href={`/applications/${id}/export`} />}>
            Export
            <ArrowRight className="size-4" data-icon="inline-end" />
          </Button>
        </div>
      </div>

      {/* Tailoring status bar */}
      {tailoring && (
        <div className="flex items-center gap-3 mb-4 rounded-lg border border-emerald/20 bg-emerald/5 px-4 py-3">
          <Loader2 className="size-4 animate-spin text-emerald" />
          <p className="text-sm text-muted-foreground">
            Running tailoring pipeline&hellip;
          </p>
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle className="size-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Left: Profile Evidence */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
              <FileText className="size-3.5" />
              Profile Evidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[calc(100dvh-280px)] pr-3">
              <div className="flex flex-col gap-4">
                {profile?.experiences.map((exp) => (
                  <div key={exp.id} className="flex flex-col gap-2">
                    <div>
                      <p className="text-sm font-medium">{exp.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {exp.organization}
                      </p>
                    </div>
                    {exp.bullets.map((bullet) => (
                      <div
                        key={bullet.id}
                        className="flex items-start gap-2.5 pl-3 border-l-2 border-border"
                      >
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {bullet.text}
                        </p>
                      </div>
                    ))}
                    <Separator />
                  </div>
                ))}

                {profile && profile.skills.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                      Skills
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {profile.skills.map((s) => (
                        <Badge
                          key={s.name}
                          variant="outline"
                          className="text-xs font-mono"
                        >
                          {s.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {!profile && (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No profile loaded.
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Center: Resume Draft */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                <Zap className="size-3.5" />
                Resume Draft
              </CardTitle>
              <Select
                value={rewriteMode}
                onValueChange={(v) => v && setRewriteMode(v)}
              >
                <SelectTrigger className="w-40 h-7 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MODES.map((mode) => (
                    <SelectItem key={mode.value} value={mode.value}>
                      {mode.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {currentMode && (
              <CardDescription className="text-xs">
                {currentMode.description}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[calc(100dvh-300px)] pr-3">
              <div className="flex flex-col gap-3">
                {bullets.length === 0 && !tailoring && (
                  <div className="flex flex-col items-center gap-3 py-12">
                    <div className="flex size-12 items-center justify-center rounded-xl bg-muted/50 ring-1 ring-border">
                      <Zap className="size-5 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground text-center">
                      No generated bullets yet.
                    </p>
                    <Button size="sm" onClick={handleTailor} disabled={!jd}>
                      <RefreshCw
                        className="size-3.5"
                        data-icon="inline-start"
                      />
                      Run Tailoring
                    </Button>
                  </div>
                )}
                {bullets.map((bullet) => (
                  <div
                    key={bullet.id}
                    className="flex flex-col gap-2 rounded-lg border border-border p-3 transition-colors hover:border-border/80"
                  >
                    <p className="text-sm leading-relaxed">{bullet.text}</p>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <ValidationBadge status={bullet.validation_status} />
                      {bullet.jd_keywords_used.map((kw) => (
                        <Badge
                          key={kw}
                          variant="outline"
                          className="text-xs font-mono border-emerald/25 text-emerald"
                        >
                          {kw}
                        </Badge>
                      ))}
                    </div>
                    {bullet.validation_notes.length > 0 && (
                      <p className="text-xs text-warning leading-relaxed">
                        {bullet.validation_notes[0]}
                      </p>
                    )}
                    <div className="flex gap-1 pt-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs px-2"
                      >
                        <RefreshCw
                          className="size-3"
                          data-icon="inline-start"
                        />
                        Regenerate
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs px-2"
                      >
                        <CheckCircle2
                          className="size-3"
                          data-icon="inline-start"
                        />
                        Approve
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs px-2 text-muted-foreground hover:text-destructive"
                      >
                        <XCircle
                          className="size-3"
                          data-icon="inline-start"
                        />
                        Reject
                      </Button>
                    </div>
                  </div>
                ))}

                {bullets.length > 0 && (
                  <>
                    <Separator />
                    <Button
                      variant="outline"
                      size="sm"
                      className="self-center"
                      onClick={handleTailor}
                      disabled={tailoring}
                    >
                      <RefreshCw
                        className="size-3.5"
                        data-icon="inline-start"
                      />
                      Re-run Tailoring
                    </Button>
                  </>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Right: JD Alignment + Validation */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
              <Shield className="size-3.5" />
              JD Alignment & Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[calc(100dvh-280px)] pr-3">
              <div className="flex flex-col gap-4">
                {/* Keyword Coverage */}
                {jd && plan?.keyword_strategy && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                      Keyword Coverage
                    </p>
                    <div className="flex flex-col gap-2">
                      {plan.keyword_strategy.covered.length > 0 && (
                        <div>
                          <span className="text-xs text-emerald font-medium">
                            Covered
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {plan.keyword_strategy.covered.map((kw) => (
                              <Badge
                                key={kw}
                                variant="outline"
                                className="text-xs font-mono border-emerald/25 text-emerald"
                              >
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {plan.keyword_strategy.not_covered.length > 0 && (
                        <div>
                          <span className="text-xs text-warning font-medium">
                            Missing
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {plan.keyword_strategy.not_covered.map((kw) => (
                              <Badge
                                key={kw}
                                variant="outline"
                                className="text-xs font-mono border-warning/25 text-warning"
                              >
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {!plan?.keyword_strategy && jd && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                      Required Skills
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {jd.required_skills.map((kw) => (
                        <Badge
                          key={kw}
                          variant="outline"
                          className="text-xs font-mono"
                        >
                          {kw}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Separator />

                {/* Validation Report */}
                {report && (
                  <>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                        Validation Report
                      </p>
                      <div className="grid grid-cols-3 gap-2 mb-3">
                        <div className="text-center rounded-lg bg-emerald/10 py-2.5">
                          <p className="text-lg font-semibold font-mono text-emerald">
                            {report.summary.supported_claims}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Supported
                          </p>
                        </div>
                        <div className="text-center rounded-lg bg-warning/10 py-2.5">
                          <p className="text-lg font-semibold font-mono text-warning">
                            {report.summary.needs_confirmation}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Confirm
                          </p>
                        </div>
                        <div className="text-center rounded-lg bg-destructive/10 py-2.5">
                          <p className="text-lg font-semibold font-mono text-destructive">
                            {report.summary.rejected_claims}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Rejected
                          </p>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                        Claims
                      </p>
                      <div className="flex flex-col gap-2">
                        {report.claims.map((claim, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 text-xs"
                          >
                            <ValidationBadge
                              status={claim.status}
                              className="shrink-0 mt-0.5"
                            />
                            <span className="text-muted-foreground leading-relaxed">
                              {claim.claim}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {report.warnings.length > 0 && (
                      <>
                        <Separator />
                        <div>
                          <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2">
                            Warnings
                          </p>
                          {report.warnings.map((warning, i) => (
                            <Alert key={i} className="mb-2">
                              <AlertTriangle className="size-3" />
                              <AlertDescription className="text-xs">
                                {warning.message}
                              </AlertDescription>
                            </Alert>
                          ))}
                        </div>
                      </>
                    )}
                  </>
                )}

                {!report && !tailoring && (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    Run tailoring to see validation results.
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
