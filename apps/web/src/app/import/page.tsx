"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  FileUp,
  AlertTriangle,
  ArrowRight,
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { importResume, saveProfile } from "@/lib/api";
import type { CanonicalProfile } from "@/lib/types";

type ImportState = "idle" | "uploading" | "parsing" | "done" | "error";

export default function ImportPage() {
  const router = useRouter();
  const [state, setState] = useState<ImportState>("idle");
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<{
    draft: Record<string, unknown>;
    warnings: string[];
  } | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  async function handleFile(file: File) {
    setFileName(file.name);
    setState("uploading");
    setErrorMessage(null);

    try {
      setState("parsing");
      const result = await importResume(file);
      setImportResult({ draft: result.draft, warnings: result.warnings });
      setState("done");
      setShowSuccess(true);
    } catch (err) {
      setState("error");
      setErrorMessage(
        err instanceof Error ? err.message : "Could not parse the uploaded file."
      );
    }
  }

  async function handleSaveAndReview() {
    if (!importResult) return;
    try {
      const draft = importResult.draft as unknown as CanonicalProfile;
      await saveProfile(draft);
      router.push("/profile");
    } catch {
      router.push("/profile");
    }
  }

  function handleReset() {
    setState("idle");
    setFileName(null);
    setImportResult(null);
    setErrorMessage(null);
    setShowSuccess(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  const draft = importResult?.draft as Record<string, unknown> | undefined;
  const experienceCount = Array.isArray(draft?.experiences) ? (draft.experiences as unknown[]).length : 0;
  const projectCount = Array.isArray(draft?.projects) ? (draft.projects as unknown[]).length : 0;
  const skillCount = Array.isArray(draft?.skills) ? (draft.skills as unknown[]).length : 0;
  const educationCount = Array.isArray(draft?.education) ? (draft.education as unknown[]).length : 0;

  return (
    <AppShell>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight mb-1">
          Import Resume
        </h1>
        <p className="text-muted-foreground text-sm mb-6">
          Upload your existing resume to build your canonical profile. Everything
          is parsed locally.
        </p>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upload File</CardTitle>
            <CardDescription>
              Supported formats: PDF, DOCX, Markdown, Plain Text
            </CardDescription>
          </CardHeader>
          <CardContent>
            {state === "idle" && (
              <label
                htmlFor="resume-upload"
                className={`flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12 cursor-pointer transition-all duration-200 ${
                  dragOver
                    ? "border-emerald bg-emerald/5 scale-[1.01]"
                    : "border-border hover:border-muted-foreground/30 hover:bg-muted/30"
                }`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <div className={`flex size-14 items-center justify-center rounded-2xl transition-colors duration-200 ${
                  dragOver ? "bg-emerald/10" : "bg-muted/50"
                }`}>
                  <FileUp className={`size-6 transition-colors duration-200 ${
                    dragOver ? "text-emerald" : "text-muted-foreground"
                  }`} />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">
                    Drop your resume here or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    PDF, DOCX, Markdown, or plain text &middot; Max 10 MB
                  </p>
                </div>
                <input
                  id="resume-upload"
                  type="file"
                  accept=".pdf,.docx,.md,.txt"
                  className="sr-only"
                  onChange={handleFileInput}
                />
              </label>
            )}

            {(state === "uploading" || state === "parsing") && (
              <div className="flex flex-col items-center gap-5 py-12">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-emerald/10">
                  <Loader2 className="size-6 text-emerald animate-spin" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">{fileName}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {state === "uploading"
                      ? "Reading file..."
                      : "Parsing sections and extracting fields..."}
                  </p>
                </div>
              </div>
            )}

            {state === "done" && (
              <div className="flex flex-col items-center gap-5 py-12">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-emerald/10">
                  <CheckCircle2 className="size-6 text-emerald" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">Resume parsed successfully</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {fileName}
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  {experienceCount > 0 && (
                    <Badge variant="secondary" className="font-mono text-xs">
                      {experienceCount} experience{experienceCount !== 1 ? "s" : ""}
                    </Badge>
                  )}
                  {projectCount > 0 && (
                    <Badge variant="secondary" className="font-mono text-xs">
                      {projectCount} project{projectCount !== 1 ? "s" : ""}
                    </Badge>
                  )}
                  {educationCount > 0 && (
                    <Badge variant="secondary" className="font-mono text-xs">
                      {educationCount} education
                    </Badge>
                  )}
                  {skillCount > 0 && (
                    <Badge variant="secondary" className="font-mono text-xs">
                      {skillCount} skill{skillCount !== 1 ? "s" : ""}
                    </Badge>
                  )}
                </div>
                <div className="flex gap-3 mt-2">
                  <Button onClick={handleSaveAndReview}>
                    Review Profile
                    <ArrowRight className="size-4 ml-1" />
                  </Button>
                  <Button variant="outline" onClick={handleReset}>
                    <RotateCcw className="size-4 mr-1" />
                    Import Another
                  </Button>
                </div>
              </div>
            )}

            {state === "error" && (
              <div className="flex flex-col items-center gap-5 py-12">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-destructive/10">
                  <AlertCircle className="size-6 text-destructive" />
                </div>
                <div className="text-center max-w-sm">
                  <p className="text-sm font-medium">Import failed</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {errorMessage ?? "Could not parse the uploaded file. Try a different format."}
                  </p>
                </div>
                <Button variant="outline" onClick={handleReset}>
                  <RotateCcw className="size-4 mr-1" />
                  Try Again
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Success dialog with warnings */}
      <Dialog open={showSuccess && (importResult?.warnings?.length ?? 0) > 0} onOpenChange={setShowSuccess}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-warning" />
              Parser Warnings
            </DialogTitle>
            <DialogDescription>
              Your resume was parsed successfully, but there were some issues to review.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
            {importResult?.warnings.map((w, i) => (
              <Alert key={i} variant="default" className="py-2">
                <AlertDescription className="text-xs">
                  {w}
                </AlertDescription>
              </Alert>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSuccess(false)}>
              Dismiss
            </Button>
            <Button onClick={handleSaveAndReview}>
              Review Profile
              <ArrowRight className="size-4 ml-1" />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
