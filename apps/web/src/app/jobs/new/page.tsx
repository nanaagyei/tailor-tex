"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  AlertTriangle,
  ArrowRight,
  Loader2,
  Target,
  Zap,
  Shield,
  ClipboardList,
  Sparkles,
  RotateCcw,
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
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { parseJD } from "@/lib/api";
import type { ParsedJobDescription } from "@/lib/types";

export default function NewJobPage() {
  const router = useRouter();
  const [jdText, setJdText] = useState("");
  const [company, setCompany] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [jd, setJd] = useState<ParsedJobDescription | null>(null);

  async function handleParse() {
    if (!jdText.trim()) return;
    setParsing(true);
    setParseError(null);
    try {
      const result = await parseJD(
        jdText,
        company || undefined,
        roleTitle || undefined
      );
      setJd(result);
    } catch (err) {
      setParseError(
        err instanceof Error ? err.message : "Failed to parse job description."
      );
    } finally {
      setParsing(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl">
        <div className="flex flex-col gap-1 mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            Job Description
          </h1>
          <p className="text-muted-foreground text-sm">
            Paste a job description to parse and match against your profile.
          </p>
        </div>

        {!jd ? (
          <Card>
            <CardHeader>
              <div className="flex items-start gap-4">
                <div className="flex size-10 items-center justify-center rounded-lg bg-emerald/10 ring-1 ring-emerald/20 shrink-0">
                  <Briefcase className="size-4 text-emerald" />
                </div>
                <div>
                  <CardTitle className="text-base">New Job Target</CardTitle>
                  <CardDescription className="mt-1">
                    Paste the full job description text below. TailorTex treats
                    this as untrusted input and will never follow instructions
                    embedded in it.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="company"
                    className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60"
                  >
                    Company
                  </label>
                  <Input
                    id="company"
                    placeholder="Apex Engineering"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="role"
                    className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60"
                  >
                    Role Title
                  </label>
                  <Input
                    id="role"
                    placeholder="Backend Software Engineer"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="jd-text"
                  className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60"
                >
                  Job Description
                </label>
                <Textarea
                  id="jd-text"
                  placeholder="Paste the full job description here..."
                  rows={12}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  className="font-mono text-sm"
                />
              </div>

              {parseError && (
                <Alert variant="destructive">
                  <AlertTriangle className="size-4" />
                  <AlertTitle>Parse failed</AlertTitle>
                  <AlertDescription>{parseError}</AlertDescription>
                </Alert>
              )}

              <div className="flex items-center justify-end">
                <Button
                  onClick={handleParse}
                  disabled={parsing || !jdText.trim()}
                >
                  {parsing ? (
                    <>
                      <Loader2
                        className="size-4 animate-spin"
                        data-icon="inline-start"
                      />
                      Parsing...
                    </>
                  ) : (
                    <>
                      Parse Job Description
                      <ArrowRight className="size-4" data-icon="inline-end" />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col gap-4">
            {/* Header card */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="flex size-10 items-center justify-center rounded-lg bg-emerald/10 ring-1 ring-emerald/20 shrink-0">
                      <Target className="size-4 text-emerald" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">
                        {jd.role_title}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {jd.company}
                        {jd.location && ` · ${jd.location}`}
                        {jd.employment_type && ` · ${jd.employment_type}`}
                        {jd.seniority && ` · ${jd.seniority}`}
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setJd(null)}
                    className="shrink-0"
                  >
                    <RotateCcw className="size-3.5" data-icon="inline-start" />
                    Edit
                  </Button>
                </div>
              </CardHeader>
            </Card>

            {/* Skills grid */}
            <div className="grid gap-4 sm:grid-cols-2">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                    <Zap className="size-3.5" />
                    Required Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1.5">
                    {jd.required_skills.map((skill) => (
                      <Badge
                        key={skill}
                        variant="secondary"
                        className="font-mono text-xs"
                      >
                        {skill}
                      </Badge>
                    ))}
                    {jd.required_skills.length === 0 && (
                      <p className="text-sm text-muted-foreground">
                        None detected
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                    <Sparkles className="size-3.5" />
                    Preferred Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1.5">
                    {jd.preferred_skills.map((skill) => (
                      <Badge
                        key={skill}
                        variant="outline"
                        className="font-mono text-xs"
                      >
                        {skill}
                      </Badge>
                    ))}
                    {jd.preferred_skills.length === 0 && (
                      <p className="text-sm text-muted-foreground">
                        None detected
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Responsibilities */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                  <ClipboardList className="size-3.5" />
                  Responsibilities
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="flex flex-col gap-2.5">
                  {jd.responsibilities.map((resp, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-3 text-sm text-foreground leading-relaxed"
                    >
                      <span className="mt-2 size-1.5 rounded-full bg-emerald/40 shrink-0" />
                      <span>{resp}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Role signals */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                  <Target className="size-3.5" />
                  Role Signals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-3">
                  {Object.entries(jd.role_signals)
                    .sort(([, a], [, b]) => b - a)
                    .map(([signal, value]) => (
                      <div key={signal} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-28 capitalize">
                          {signal.replace("_", " ")}
                        </span>
                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald rounded-full transition-all"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-muted-foreground w-10 text-right">
                          {(value * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Prompt injection warning */}
            {jd.prompt_injection_flags.length > 0 && (
              <Alert variant="destructive">
                <Shield className="size-4" />
                <AlertTitle>Prompt injection detected</AlertTitle>
                <AlertDescription>
                  This job description contains suspicious patterns that may
                  attempt to manipulate the AI. These have been flagged and will
                  be ignored during tailoring.
                </AlertDescription>
              </Alert>
            )}

            <Separator />

            <div className="flex items-center justify-end">
              <Button
                onClick={() => router.push(`/applications/${jd.job_id}`)}
              >
                Start Tailoring
                <ArrowRight className="size-4" data-icon="inline-end" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
