"use client";

import { useState, useEffect, use } from "react";
import { ArrowLeft, Columns, Rows } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
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
  ParsedJobDescription,
  CanonicalProfile,
  GeneratedBullet,
} from "@/lib/types";

type DiffLayout = "side-by-side" | "inline";

interface DiffItem {
  id: string;
  original: string;
  generated: string;
  validation_status: "supported" | "needs_confirmation" | "rejected";
}

export default function DiffViewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [layout, setLayout] = useState<DiffLayout>("inline");
  const [jd, setJd] = useState<ParsedJobDescription | null>(null);
  const [diffs, setDiffs] = useState<DiffItem[]>([]);
  const [loading, setLoading] = useState(true);
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

        let profile: CanonicalProfile | null = null;
        if (profiles.length > 0) {
          profile = await getProfile(profiles[0]);
        }

        const result = await tailorResume({
          jd_id: id,
          profile_id: profile?.profile_id,
        });

        // Build diff items by matching generated bullets to originals
        const originalBullets: Record<string, string> = {};
        if (profile) {
          for (const exp of profile.experiences) {
            for (const b of exp.bullets) {
              originalBullets[b.id] = b.text;
            }
          }
          for (const proj of profile.projects) {
            for (const b of proj.bullets) {
              originalBullets[b.id] = b.text;
            }
          }
        }

        const diffItems: DiffItem[] = result.generated_bullets.map(
          (gen: GeneratedBullet) => {
            const sourceId = gen.source_bullet_ids[0] ?? "";
            return {
              id: gen.id,
              original: originalBullets[sourceId] ?? "(original not found)",
              generated: gen.text,
              validation_status: gen.validation_status,
            };
          }
        );
        setDiffs(diffItems);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load diff."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-5xl flex flex-col gap-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </AppShell>
    );
  }

  if (error && !jd) {
    return (
      <AppShell>
        <EmptyState
          title="Could not load diff"
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
            <h1 className="text-2xl font-semibold tracking-tight">
              Diff View
            </h1>
            <p className="text-sm text-muted-foreground">
              {jd?.role_title} at {jd?.company} &mdash; original vs. generated
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              render={<a href={`/applications/${id}`} />}
            >
              <ArrowLeft className="size-4" data-icon="inline-start" />
              Back to Workspace
            </Button>
            <div className="flex items-center rounded-md border border-border">
              <Button
                variant={layout === "inline" ? "secondary" : "ghost"}
                size="sm"
                className="rounded-r-none h-8"
                onClick={() => setLayout("inline")}
              >
                <Rows className="size-4" />
              </Button>
              <Button
                variant={layout === "side-by-side" ? "secondary" : "ghost"}
                size="sm"
                className="rounded-l-none h-8"
                onClick={() => setLayout("side-by-side")}
              >
                <Columns className="size-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="inline-block size-3 rounded-sm bg-destructive/20 border border-destructive/30" />
            Original
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block size-3 rounded-sm bg-emerald/20 border border-emerald/30" />
            Generated
          </div>
        </div>

        <div className="flex flex-col gap-4">
          {diffs.map((diff, i) => (
            <Card key={diff.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm text-muted-foreground font-mono">
                    Bullet {i + 1}
                  </CardTitle>
                  <ValidationBadge status={diff.validation_status} />
                </div>
              </CardHeader>
              <CardContent>
                {layout === "inline" ? (
                  <div className="flex flex-col gap-3">
                    <div className="rounded-md bg-destructive/5 border border-destructive/15 p-3">
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Original
                      </p>
                      <p className="text-sm leading-relaxed">{diff.original}</p>
                    </div>
                    <div className="rounded-md bg-emerald/5 border border-emerald/15 p-3">
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Generated
                      </p>
                      <p className="text-sm leading-relaxed">
                        {diff.generated}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-md border border-destructive/20 bg-destructive/5 p-4">
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Original
                      </p>
                      <p className="text-sm leading-relaxed text-foreground">
                        {diff.original}
                      </p>
                    </div>
                    <div className="rounded-md border border-emerald/20 bg-emerald/5 p-4">
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Generated
                      </p>
                      <p className="text-sm leading-relaxed text-foreground">
                        {diff.generated}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}

          {diffs.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              No diff data available.
            </p>
          )}
        </div>

        <Separator className="my-6" />

        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground font-mono">
            {diffs.length} bullets &middot;{" "}
            {diffs.filter((d) => d.validation_status === "supported").length}{" "}
            supported &middot;{" "}
            {
              diffs.filter((d) => d.validation_status === "needs_confirmation")
                .length
            }{" "}
            needs confirmation
          </p>
          <Button
            size="sm"
            render={<a href={`/applications/${id}/export`} />}
          >
            Continue to Export
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
