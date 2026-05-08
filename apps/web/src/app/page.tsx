"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Upload,
  Play,
  Settings,
  Shield,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listProfiles, listApplications, checkHealth } from "@/lib/api";

const actions = [
  {
    title: "Import Resume",
    description: "Upload your existing resume to build your canonical profile.",
    icon: Upload,
    href: "/import",
    accent: "emerald" as const,
  },
  {
    title: "Try Demo",
    description: "See TailorTex in action with sample data.",
    icon: Play,
    href: "/profile",
    accent: "blue" as const,
  },
  {
    title: "Configure Provider",
    description: "Set up an LLM provider or use rule-based mode.",
    icon: Settings,
    href: "/settings",
    accent: "zinc" as const,
  },
];

const features = [
  { icon: Shield, text: "Your data stays on your machine" },
  { icon: CheckCircle2, text: "Every claim traces to approved evidence" },
  { icon: Zap, text: "No accounts, no telemetry, no paywalls" },
];

export default function WelcomePage() {
  const [profileCount, setProfileCount] = useState<number | null>(null);
  const [appCount, setAppCount] = useState<number | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        await checkHealth();
        setApiOnline(true);
        const [profiles, apps] = await Promise.all([
          listProfiles(),
          listApplications(),
        ]);
        setProfileCount(profiles.length);
        setAppCount(apps.length);
      } catch {
        setApiOnline(false);
      }
    }
    loadStatus();
  }, []);

  return (
    <AppShell>
      <div className="grid gap-10 lg:grid-cols-2 lg:gap-16 items-start">
        {/* Left — Hero */}
        <div className="flex flex-col gap-8 lg:py-6">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Image
                src="/logo.png"
                alt="TailorTex logo"
                width={44}
                height={44}
                priority
                className="size-11 rounded-xl"
              />
              <div>
                <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
                  TailorTex
                </h1>
                <p className="text-xs text-muted-foreground">
                  Resume tailoring workbench
                </p>
              </div>
            </div>

            <p className="text-muted-foreground leading-relaxed max-w-md">
              Import your resume, parse a job description, and generate a
              truthful, ATS-readable LaTeX resume — all without sending your
              data anywhere.
            </p>
          </div>

          <div className="flex flex-col gap-2.5">
            {features.map((f) => (
              <div
                key={f.text}
                className="flex items-center gap-3 rounded-lg border border-border/50 bg-card/50 px-4 py-2.5"
              >
                <f.icon className="size-4 text-emerald shrink-0" />
                <span className="text-sm text-muted-foreground">{f.text}</span>
              </div>
            ))}
          </div>

          {/* Status bar */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className={
                apiOnline === true
                  ? "border-emerald/30 text-emerald"
                  : apiOnline === false
                    ? "border-destructive/30 text-destructive"
                    : "text-muted-foreground"
              }
            >
              {apiOnline === null ? (
                "Checking..."
              ) : apiOnline ? (
                <><CheckCircle2 className="size-3 mr-1" /> API Online</>
              ) : (
                <><XCircle className="size-3 mr-1" /> API Offline</>
              )}
            </Badge>
            {profileCount !== null && (
              <Badge variant="outline" className="text-muted-foreground font-mono text-xs">
                {profileCount} profile{profileCount !== 1 ? "s" : ""}
              </Badge>
            )}
            {appCount !== null && appCount > 0 && (
              <Badge variant="outline" className="text-muted-foreground font-mono text-xs">
                {appCount} application{appCount !== 1 ? "s" : ""}
              </Badge>
            )}
          </div>
        </div>

        {/* Right — Action cards */}
        <div className="flex flex-col gap-3 lg:py-6">
          <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-1">
            Get Started
          </p>
          {actions.map((action) => (
            <Link key={action.href} href={action.href}>
              <Card className="group cursor-pointer transition-all duration-200 hover:border-emerald/25 hover:shadow-sm hover:shadow-emerald/5">
                <CardHeader className="flex flex-row items-center gap-4 py-4">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border group-hover:bg-emerald/10 group-hover:ring-emerald/20 transition-all duration-200">
                    <action.icon className="size-4 text-muted-foreground group-hover:text-emerald transition-colors duration-200" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-sm font-medium">
                      {action.title}
                    </CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      {action.description}
                    </CardDescription>
                  </div>
                  <ArrowRight className="size-4 text-muted-foreground/40 -translate-x-1 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200 shrink-0" />
                </CardHeader>
              </Card>
            </Link>
          ))}

          {!apiOnline && apiOnline !== null && (
            <div className="rounded-lg border border-warning/20 bg-warning/5 px-4 py-3 mt-1">
              <p className="text-xs text-warning font-medium mb-0.5">
                API server is not running
              </p>
              <p className="text-xs text-muted-foreground">
                Start the server with{" "}
                <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">
                  make dev
                </code>{" "}
                to enable all features.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
