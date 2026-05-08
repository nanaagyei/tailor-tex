"use client";

import { useState, useEffect, use } from "react";
import {
  ArrowLeft,
  Download,
  FileText,
  FileArchive,
  FileCheck,
  Copy,
  Check,
  Monitor,
  Upload,
  Terminal,
  Info,
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
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/empty-state";
import {
  getApplication,
  listProfiles,
  renderResume,
  tailorResume,
} from "@/lib/api";
import type { ParsedJobDescription, ValidationReport } from "@/lib/types";

export default function ExportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [copied, setCopied] = useState(false);
  const [jd, setJd] = useState<ParsedJobDescription | null>(null);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [texContent, setTexContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderGuideOpen, setRenderGuideOpen] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [appData, profiles] = await Promise.all([
          getApplication(id),
          listProfiles(),
        ]);
        const parsedJd = appData as unknown as ParsedJobDescription;
        setJd(parsedJd);

        const profileId = profiles.length > 0 ? profiles[0] : "default";

        const [renderResult, tailorResult] = await Promise.all([
          renderResume({ jd_id: id, profile_id: profileId }),
          tailorResume({ jd_id: id, profile_id: profileId }),
        ]);

        setTexContent(renderResult.tex);
        setReport(tailorResult.validation);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load export data."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  function handleCopy() {
    if (!texContent) return;
    navigator.clipboard.writeText(texContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownloadTex() {
    if (!texContent) return;
    const blob = new Blob([texContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resume-${id}.tex`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-5xl flex flex-col gap-4">
          <Skeleton className="h-8 w-48" />
          <div className="grid gap-4 lg:grid-cols-5">
            <div className="lg:col-span-2 flex flex-col gap-4">
              <Skeleton className="h-32" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
            <Skeleton className="lg:col-span-3 h-96" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error && !jd) {
    return (
      <AppShell>
        <EmptyState
          title="Could not load export"
          description={error}
          action={{ label: "Back", href: `/applications/${id}` }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-5xl">
        <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Export</h1>
            <p className="text-sm text-muted-foreground">
              {jd?.role_title} at {jd?.company}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            render={<a href={`/applications/${id}`} />}
          >
            <ArrowLeft className="size-4" data-icon="inline-start" />
            Back to Workspace
          </Button>
        </div>

        <div className="grid gap-4 lg:grid-cols-5">
          {/* Left: Export options */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            {/* Validation summary */}
            {report && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60">
                    Validation Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center rounded-lg bg-emerald/10 py-2.5">
                      <p className="text-lg font-semibold font-mono text-emerald">
                        {report.summary.supported_claims}
                      </p>
                      <p className="text-xs text-muted-foreground">Supported</p>
                    </div>
                    <div className="text-center rounded-lg bg-warning/10 py-2.5">
                      <p className="text-lg font-semibold font-mono text-warning">
                        {report.summary.needs_confirmation}
                      </p>
                      <p className="text-xs text-muted-foreground">Confirm</p>
                    </div>
                    <div className="text-center rounded-lg bg-destructive/10 py-2.5">
                      <p className="text-lg font-semibold font-mono text-destructive">
                        {report.summary.rejected_claims}
                      </p>
                      <p className="text-xs text-muted-foreground">Rejected</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                    <span>LaTeX errors: {report.summary.latex_errors}</span>
                    <Badge
                      variant={
                        report.status === "passed" ? "secondary" : "outline"
                      }
                      className="text-xs"
                    >
                      {report.status === "passed"
                        ? "Clean"
                        : report.status === "passed_with_warnings"
                          ? "Warnings"
                          : "Issues"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Download options */}
            <div className="flex flex-col gap-3">
              <Card
                className="group cursor-pointer transition-colors hover:border-emerald/30"
                onClick={handleDownloadTex}
              >
                <CardHeader className="pb-0">
                  <div className="flex items-start gap-3">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border group-hover:bg-emerald/10 group-hover:ring-emerald/20 transition-colors">
                      <FileText className="size-4 text-muted-foreground group-hover:text-emerald transition-colors" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-sm flex items-center gap-2">
                        LaTeX Source
                        <Download className="size-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </CardTitle>
                      <CardDescription className="text-xs mt-0.5">
                        Download the .tex file for local compilation or paste
                        into any LaTeX editor.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>

              <Card className="group cursor-pointer transition-colors hover:border-emerald/30">
                <CardHeader className="pb-0">
                  <div className="flex items-start gap-3">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border group-hover:bg-emerald/10 group-hover:ring-emerald/20 transition-colors">
                      <FileArchive className="size-4 text-muted-foreground group-hover:text-emerald transition-colors" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-sm flex items-center gap-2">
                        Overleaf Bundle
                        <Download className="size-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </CardTitle>
                      <CardDescription className="text-xs mt-0.5">
                        ZIP archive with main.tex and README. Upload directly to
                        Overleaf.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>

              <Card className="group cursor-pointer transition-colors hover:border-emerald/30">
                <CardHeader className="pb-0">
                  <div className="flex items-start gap-3">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border group-hover:bg-emerald/10 group-hover:ring-emerald/20 transition-colors">
                      <FileCheck className="size-4 text-muted-foreground group-hover:text-emerald transition-colors" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-sm flex items-center gap-2">
                        Validation Report
                        <Download className="size-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </CardTitle>
                      <CardDescription className="text-xs mt-0.5">
                        Markdown report with all claims, evidence, and warnings.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </div>

            {/* Render to PDF section */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 flex items-center gap-2">
                  <Monitor className="size-3.5" />
                  Render to PDF
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  You need a LaTeX engine to compile this .tex file into a PDF.
                  Pick whichever option works best for you:
                </p>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => setRenderGuideOpen(true)}
                >
                  <Info className="size-3.5" data-icon="inline-start" />
                  How to render my resume
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Right: LaTeX preview */}
          <Card className="lg:col-span-3">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60">
                  LaTeX Preview
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={handleCopy}
                  disabled={!texContent}
                >
                  {copied ? (
                    <>
                      <Check className="size-3" data-icon="inline-start" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="size-3" data-icon="inline-start" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[calc(100dvh-280px)]">
                {texContent ? (
                  <pre className="text-xs font-mono leading-relaxed text-muted-foreground whitespace-pre-wrap wrap-break-word">
                    {texContent}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-12">
                    No LaTeX output available.
                  </p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <Separator className="my-6" />

        <p className="text-xs text-muted-foreground font-mono">
          Workspace: ~/.tailortex &middot; Application: {jd?.role_title} at{" "}
          {jd?.company}
        </p>
      </div>

      {/* Render Guide Dialog */}
      <Dialog open={renderGuideOpen} onOpenChange={setRenderGuideOpen}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>How to Render Your Resume</DialogTitle>
            <DialogDescription>
              Choose the method that works best for your setup.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-5">
            {/* Option 1: Overleaf */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-lg bg-emerald/10 ring-1 ring-emerald/20 shrink-0">
                  <Upload className="size-3.5 text-emerald" />
                </div>
                <div>
                  <p className="text-sm font-medium">
                    Overleaf (recommended, no install)
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Free online LaTeX editor with instant PDF preview
                  </p>
                </div>
              </div>
              <ol className="flex flex-col gap-1.5 ml-11 text-xs text-muted-foreground leading-relaxed list-decimal list-outside">
                <li>Download the <strong>.tex file</strong> or <strong>Overleaf Bundle</strong> above</li>
                <li>Go to <strong>overleaf.com</strong> and sign in (or create a free account)</li>
                <li>Click <strong>New Project &rarr; Upload Project</strong> (for the ZIP) or <strong>Blank Project</strong> then paste the .tex content</li>
                <li>Hit <strong>Recompile</strong> &mdash; your PDF appears on the right</li>
                <li>Click the download icon to save your PDF</li>
              </ol>
            </div>

            <Separator />

            {/* Option 2: Tectonic */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border shrink-0">
                  <Terminal className="size-3.5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">
                    Tectonic (lightweight CLI)
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Self-contained LaTeX engine, auto-downloads packages
                  </p>
                </div>
              </div>
              <div className="ml-11 rounded-lg bg-muted/50 border border-border p-3">
                <pre className="text-xs font-mono text-foreground leading-relaxed">
{`# Install (macOS)
brew install tectonic

# Install (Linux/WSL)
curl --proto '=https' --tlsv1.2 \\
  -fsSL https://drop-sh.fullyjustified.net | sh

# Compile
tectonic resume.tex`}
                </pre>
              </div>
            </div>

            <Separator />

            {/* Option 3: latexmk */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border shrink-0">
                  <Terminal className="size-3.5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">
                    latexmk (full TeX Live)
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Part of TeX Live / MacTeX &mdash; most flexible
                  </p>
                </div>
              </div>
              <div className="ml-11 rounded-lg bg-muted/50 border border-border p-3">
                <pre className="text-xs font-mono text-foreground leading-relaxed">
{`# Install (macOS)
brew install --cask mactex-no-gui

# Install (Ubuntu/Debian)
sudo apt install texlive-full latexmk

# Compile
latexmk -pdf -interaction=nonstopmode resume.tex`}
                </pre>
              </div>
            </div>

            <Separator />

            {/* Option 4: VS Code */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border shrink-0">
                  <Monitor className="size-3.5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">
                    VS Code + LaTeX Workshop
                  </p>
                  <p className="text-xs text-muted-foreground">
                    IDE-integrated with live preview
                  </p>
                </div>
              </div>
              <ol className="flex flex-col gap-1.5 ml-11 text-xs text-muted-foreground leading-relaxed list-decimal list-outside">
                <li>Install the <strong>LaTeX Workshop</strong> extension</li>
                <li>Make sure <strong>latexmk</strong> or <strong>tectonic</strong> is on your PATH</li>
                <li>Open the .tex file &mdash; it compiles on save with a live PDF preview panel</li>
              </ol>
            </div>
          </div>

          <Alert className="mt-2">
            <Info className="size-4" />
            <AlertDescription className="text-xs">
              <strong>TailorTex is local-first.</strong> Your resume data never leaves
              your machine. The .tex file is self-contained and renders the same
              everywhere.
            </AlertDescription>
          </Alert>

          <DialogFooter showCloseButton />
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
