"use client";

import { useState, useEffect } from "react";
import { Shield, Eye, EyeOff, Moon, Sun, Loader2, Check } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { getConfig, updateConfig, listProfiles, listApplications } from "@/lib/api";

export default function SettingsPage() {
  const [provider, setProvider] = useState("none");
  const [endpoint, setEndpoint] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);

  const [redactPII, setRedactPII] = useState(true);
  const [requireConsent, setRequireConsent] = useState(true);
  const [workspacePath, setWorkspacePath] = useState("~/.tailortex");
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark") ? "dark" : "light";
    }
    return "dark";
  });

  const [profileCount, setProfileCount] = useState(0);
  const [appCount, setAppCount] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [config, profiles, apps] = await Promise.all([
          getConfig().catch(() => ({})),
          listProfiles().catch(() => []),
          listApplications().catch(() => []),
        ]);
        setProfileCount(profiles.length);
        setAppCount(apps.length);

        if (config && typeof config === "object") {
          const c = config as Record<string, unknown>;
          if (c.provider) setProvider(c.provider as string);
          if (c.endpoint) setEndpoint(c.endpoint as string);
          if (c.model) setModel(c.model as string);
          if (c.api_key) setApiKey(c.api_key as string);
          if (c.redact_pii !== undefined) setRedactPII(c.redact_pii as boolean);
          if (c.require_consent !== undefined)
            setRequireConsent(c.require_consent as boolean);
          if (c.workspace_path) setWorkspacePath(c.workspace_path as string);
        }
      } catch {
        // use defaults
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    try {
      await updateConfig({
        provider,
        endpoint,
        model,
        api_key: apiKey,
        redact_pii: redactPII,
        require_consent: requireConsent,
        workspace_path: workspacePath,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight mb-1">
          Settings
        </h1>
        <p className="text-muted-foreground text-sm mb-6">
          Configure your LLM provider, privacy preferences, and workspace.
        </p>

        <div className="flex flex-col gap-6">
          {/* LLM Provider */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">LLM Provider</CardTitle>
              <CardDescription>
                Choose an LLM backend for AI-assisted rewriting. Use
                &quot;None&quot; for rule-based mode with no external calls.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="provider" className="text-sm font-medium">
                  Provider
                </label>
                <Select
                  value={provider}
                  onValueChange={(v) => v && setProvider(v)}
                >
                  <SelectTrigger id="provider" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      None (Rule-Based Only)
                    </SelectItem>
                    <SelectItem value="openai">OpenAI-Compatible</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    <SelectItem value="lmstudio">LM Studio (Local)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {provider !== "none" && (
                <>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="endpoint" className="text-sm font-medium">
                      Endpoint URL
                    </label>
                    <Input
                      id="endpoint"
                      placeholder={
                        provider === "ollama"
                          ? "http://localhost:11434"
                          : provider === "lmstudio"
                            ? "http://localhost:1234/v1"
                            : "https://api.example.com/v1"
                      }
                      value={endpoint}
                      onChange={(e) => setEndpoint(e.target.value)}
                      className="font-mono text-sm"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="model" className="text-sm font-medium">
                      Model
                    </label>
                    <Input
                      id="model"
                      placeholder={
                        provider === "anthropic"
                          ? "claude-sonnet-4-5-20250514"
                          : provider === "ollama"
                            ? "llama3.1:8b"
                            : "gpt-4o"
                      }
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="font-mono text-sm"
                    />
                  </div>

                  {(provider === "openai" || provider === "anthropic") && (
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="api-key" className="text-sm font-medium">
                        API Key
                      </label>
                      <div className="flex gap-2">
                        <Input
                          id="api-key"
                          type={showKey ? "text" : "password"}
                          placeholder="sk-..."
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          className="font-mono text-sm flex-1"
                        />
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => setShowKey(!showKey)}
                          className="shrink-0"
                        >
                          {showKey ? (
                            <EyeOff className="size-4" />
                          ) : (
                            <Eye className="size-4" />
                          )}
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Stored locally in your workspace. Never sent anywhere
                        except the configured provider endpoint.
                      </p>
                    </div>
                  )}

                  {(provider === "ollama" || provider === "lmstudio") && (
                    <div className="rounded-md bg-emerald/10 border border-emerald/20 px-3 py-2">
                      <div className="flex items-center gap-2 text-xs text-emerald">
                        <Shield className="size-3.5" />
                        Local provider &mdash; no data leaves your machine.
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* Privacy */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shield className="size-4 text-emerald" />
                Privacy
              </CardTitle>
              <CardDescription>
                Control how your data is handled when using cloud LLM providers.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex flex-col gap-0.5">
                  <p className="text-sm font-medium">Redact PII</p>
                  <p className="text-xs text-muted-foreground">
                    Replace names, emails, and companies with placeholders before
                    sending to cloud providers.
                  </p>
                </div>
                <Switch checked={redactPII} onCheckedChange={setRedactPII} />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex flex-col gap-0.5">
                  <p className="text-sm font-medium">
                    Require consent for cloud calls
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Show a confirmation dialog before each cloud LLM request.
                  </p>
                </div>
                <Switch
                  checked={requireConsent}
                  onCheckedChange={setRequireConsent}
                />
              </div>
            </CardContent>
          </Card>

          {/* Workspace */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Workspace</CardTitle>
              <CardDescription>
                Where TailorTex stores profiles, applications, and exports.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="workspace-path"
                  className="text-sm font-medium"
                >
                  Workspace Path
                </label>
                <Input
                  id="workspace-path"
                  value={workspacePath}
                  onChange={(e) => setWorkspacePath(e.target.value)}
                  className="font-mono text-sm"
                />
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <Badge variant="outline" className="font-mono text-xs">
                  {profileCount} profile{profileCount !== 1 ? "s" : ""}
                </Badge>
                <Badge variant="outline" className="font-mono text-xs">
                  {appCount} application{appCount !== 1 ? "s" : ""}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Appearance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex flex-col gap-0.5">
                  <p className="text-sm font-medium">Theme</p>
                  <p className="text-xs text-muted-foreground">
                    Switch between dark and light mode.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const next = theme === "dark" ? "light" : "dark";
                    setTheme(next);
                    document.documentElement.classList.toggle("dark", next === "dark");
                    localStorage.setItem("tailortex-theme", next);
                  }}
                >
                  {theme === "dark" ? (
                    <>
                      <Moon className="size-4" data-icon="inline-start" />
                      Dark
                    </>
                  ) : (
                    <>
                      <Sun className="size-4" data-icon="inline-start" />
                      Light
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Separator />

          <Button className="self-end" onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
                Saving...
              </>
            ) : saved ? (
              <>
                <Check className="size-4" data-icon="inline-start" />
                Saved
              </>
            ) : (
              "Save Settings"
            )}
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
