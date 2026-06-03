"use client";

import { useState, useEffect, useCallback } from "react";
import {
  User,
  Briefcase,
  GraduationCap,
  Code,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Loader2,
  MapPin,
  Mail,
  ExternalLink,
  Award,
  Layers,
  Pencil,
  Plus,
  Trash2,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/empty-state";
import { ConfidenceBadge } from "@/components/confidence-badge";
import { getProfile, listProfiles, saveProfile } from "@/lib/api";
import type {
  CanonicalProfile,
  Experience,
  Project,
  Education,
  Owner,
} from "@/lib/types";

// ── Helpers ────────────────────────────────────────────

function EditButton({ onClick }: { onClick?: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className="size-7 text-muted-foreground hover:text-foreground"
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
    >
      <Pencil className="size-3.5" />
    </Button>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60">
      {children}
    </label>
  );
}

function TagInput({
  tags,
  onChange,
  placeholder,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");

  function addTag(raw: string) {
    const tag = raw.trim();
    if (tag && !tags.includes(tag)) {
      onChange([...tags, tag]);
    }
    setInput("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(input);
    }
    if (e.key === "Backspace" && input === "" && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  }

  function handleBlur() {
    if (input.trim()) addTag(input);
  }

  return (
    <div className="flex flex-wrap gap-1.5 rounded-lg border border-input bg-transparent px-2.5 py-1.5 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 dark:bg-input/30">
      {tags.map((tag) => (
        <Badge
          key={tag}
          variant="secondary"
          className="gap-1 text-xs font-mono pr-1"
        >
          {tag}
          <button
            type="button"
            className="ml-0.5 rounded-sm hover:bg-foreground/10 p-0.5"
            onClick={() => onChange(tags.filter((t) => t !== tag))}
          >
            <span className="sr-only">Remove {tag}</span>
            <span className="text-[10px] leading-none">&times;</span>
          </button>
        </Badge>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={tags.length === 0 ? placeholder : "Add..."}
        className="flex-1 min-w-[80px] bg-transparent text-sm outline-none placeholder:text-muted-foreground"
      />
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────

export default function ProfilePage() {
  const [profile, setProfile] = useState<CanonicalProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const profiles = await listProfiles();
        if (profiles.length > 0) {
          const p = await getProfile(profiles[0]);
          setProfile(p);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load profile."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const persist = useCallback(
    async (updated: CanonicalProfile) => {
      setProfile(updated);
      setSaving(true);
      try {
        await saveProfile({
          ...updated,
          updated_at: new Date().toISOString(),
        });
      } catch {
        // save failed silently — profile stays in local state
      } finally {
        setSaving(false);
      }
    },
    []
  );

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-4xl flex flex-col gap-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </AppShell>
    );
  }

  if (error || !profile) {
    return (
      <AppShell>
        <EmptyState
          title="No profile found"
          description={
            error ?? "Import a resume to create your canonical profile."
          }
          action={{ label: "Import Resume", href: "/import" }}
        />
      </AppShell>
    );
  }

  const totalBullets = profile.experiences.reduce(
    (sum, exp) => sum + exp.bullets.length,
    0
  );

  return (
    <AppShell>
      <div className="max-w-4xl">
        <div className="flex flex-col gap-1 mb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Profile Review
            </h1>
            <p className="text-muted-foreground text-sm">
              Review and edit your canonical profile before tailoring.
            </p>
          </div>
          <div className="flex items-center gap-2 mt-3 sm:mt-0">
            {saving && (
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Loader2 className="size-3 animate-spin" />
                Saving...
              </span>
            )}
            <Badge variant="outline" className="text-xs font-mono">
              <CheckCircle2 className="size-3 text-emerald mr-1" />
              Auto-saved
            </Badge>
          </div>
        </div>

        {/* Owner card */}
        <OwnerCard owner={profile.owner} onSave={(owner) => persist({ ...profile, owner })} />

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="rounded-lg border border-border bg-card/50 px-4 py-3">
            <p className="text-xs text-muted-foreground">Experiences</p>
            <p className="text-xl font-semibold font-mono mt-0.5">
              {profile.experiences.length}
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card/50 px-4 py-3">
            <p className="text-xs text-muted-foreground">Projects</p>
            <p className="text-xl font-semibold font-mono mt-0.5">
              {profile.projects.length}
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card/50 px-4 py-3">
            <p className="text-xs text-muted-foreground">Skills</p>
            <p className="text-xl font-semibold font-mono mt-0.5">
              {profile.skills.length}
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card/50 px-4 py-3">
            <p className="text-xs text-muted-foreground">Bullets</p>
            <p className="text-xl font-semibold font-mono mt-0.5">
              {totalBullets}
            </p>
          </div>
        </div>

        <Tabs defaultValue="experience">
          <TabsList className="mb-4">
            <TabsTrigger value="experience">
              <Briefcase className="size-4" data-icon="inline-start" />
              Experience
            </TabsTrigger>
            <TabsTrigger value="projects">
              <Code className="size-4" data-icon="inline-start" />
              Projects
            </TabsTrigger>
            <TabsTrigger value="education">
              <GraduationCap className="size-4" data-icon="inline-start" />
              Education
            </TabsTrigger>
            <TabsTrigger value="skills">
              <Layers className="size-4" data-icon="inline-start" />
              Skills
            </TabsTrigger>
          </TabsList>

          <TabsContent value="experience" className="flex flex-col gap-4">
            {profile.experiences.map((exp, idx) => (
              <ExperienceCard
                key={exp.id}
                experience={exp}
                onSave={(updated) => {
                  const exps = [...profile.experiences];
                  exps[idx] = updated;
                  persist({ ...profile, experiences: exps });
                }}
                onDelete={() => {
                  persist({
                    ...profile,
                    experiences: profile.experiences.filter(
                      (_, i) => i !== idx
                    ),
                  });
                }}
              />
            ))}
            {profile.experiences.length === 0 && (
              <EmptyState
                icon={Briefcase}
                title="No experiences"
                description="No work experience entries found in your profile."
              />
            )}
          </TabsContent>

          <TabsContent value="projects" className="flex flex-col gap-4">
            {profile.projects.map((proj, idx) => (
              <ProjectCard
                key={proj.id}
                project={proj}
                onSave={(updated) => {
                  const projs = [...profile.projects];
                  projs[idx] = updated;
                  persist({ ...profile, projects: projs });
                }}
                onDelete={() => {
                  persist({
                    ...profile,
                    projects: profile.projects.filter((_, i) => i !== idx),
                  });
                }}
              />
            ))}
            {profile.projects.length === 0 && (
              <EmptyState
                icon={Code}
                title="No projects"
                description="No project entries found in your profile."
              />
            )}
          </TabsContent>

          <TabsContent value="education" className="flex flex-col gap-4">
            {profile.education.map((edu, idx) => (
              <EducationCard
                key={edu.id}
                education={edu}
                onSave={(updated) => {
                  const edus = [...profile.education];
                  edus[idx] = updated;
                  persist({ ...profile, education: edus });
                }}
                onDelete={() => {
                  persist({
                    ...profile,
                    education: profile.education.filter((_, i) => i !== idx),
                  });
                }}
              />
            ))}
            {profile.education.length === 0 && (
              <EmptyState
                icon={GraduationCap}
                title="No education"
                description="No education entries found in your profile."
              />
            )}
          </TabsContent>

          <TabsContent value="skills">
            <SkillsCard
              skills={profile.skills}
              onSave={(skills) => persist({ ...profile, skills })}
            />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

// ── Owner Card with Edit ───────────────────────────────

function OwnerCard({
  owner,
  onSave,
}: {
  owner: Owner;
  onSave: (owner: Owner) => void;
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(owner);

  function handleOpen() {
    setDraft(owner);
    setOpen(true);
  }

  function handleSave() {
    onSave(draft);
    setOpen(false);
  }

  return (
    <>
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="flex size-12 items-center justify-center rounded-xl bg-emerald/10 ring-1 ring-emerald/20 shrink-0">
              <User className="size-5 text-emerald" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-lg">
                  {owner.full_name}
                </CardTitle>
                <EditButton onClick={handleOpen} />
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5">
                {owner.email && (
                  <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Mail className="size-3.5" />
                    {owner.email}
                  </span>
                )}
                {owner.location && (
                  <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <MapPin className="size-3.5" />
                    {owner.location}
                  </span>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        {owner.links.length > 0 && (
          <CardContent className="pt-0">
            <Separator className="mb-4" />
            <div className="flex flex-wrap gap-2">
              {owner.links.map((link) => (
                <Badge
                  key={link.url}
                  variant="outline"
                  className="gap-1.5 font-normal"
                >
                  <ExternalLink className="size-3" />
                  {link.label}
                </Badge>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Contact Info</DialogTitle>
            <DialogDescription>
              Update your name, email, location, and links.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Full Name</FieldLabel>
              <Input
                value={draft.full_name}
                onChange={(e) =>
                  setDraft({ ...draft, full_name: e.target.value })
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Email</FieldLabel>
              <Input
                value={draft.email ?? ""}
                onChange={(e) =>
                  setDraft({ ...draft, email: e.target.value || null })
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Phone</FieldLabel>
              <Input
                value={draft.phone ?? ""}
                onChange={(e) =>
                  setDraft({ ...draft, phone: e.target.value || null })
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Location</FieldLabel>
              <Input
                value={draft.location ?? ""}
                onChange={(e) =>
                  setDraft({ ...draft, location: e.target.value || null })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleSave}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Experience Card with Edit ──────────────────────────

function ExperienceCard({
  experience,
  onSave,
  onDelete,
}: {
  experience: Experience;
  onSave: (exp: Experience) => void;
  onDelete: () => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const [editOpen, setEditOpen] = useState(false);
  const [draft, setDraft] = useState(experience);

  function handleOpen() {
    setDraft(experience);
    setEditOpen(true);
  }

  function handleSave() {
    onSave(draft);
    setEditOpen(false);
  }

  function updateBullet(idx: number, text: string) {
    const bullets = [...draft.bullets];
    bullets[idx] = { ...bullets[idx], text };
    setDraft({ ...draft, bullets });
  }

  function removeBullet(idx: number) {
    setDraft({
      ...draft,
      bullets: draft.bullets.filter((_, i) => i !== idx),
    });
  }

  function addBullet() {
    setDraft({
      ...draft,
      bullets: [
        ...draft.bullets,
        {
          id: crypto.randomUUID(),
          text: "",
          skills: [],
          metrics: [],
          evidence_ids: [],
          approved: false,
        },
      ],
    });
  }

  return (
    <>
      <Card>
        <CardHeader
          className="cursor-pointer select-none"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-start gap-4">
            <div className="flex size-10 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border shrink-0 mt-0.5">
              <Briefcase className="size-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    {experience.title}
                    {expanded ? (
                      <ChevronDown className="size-3.5 text-muted-foreground/50" />
                    ) : (
                      <ChevronRight className="size-3.5 text-muted-foreground/50" />
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {experience.organization}
                    {experience.location && ` · ${experience.location}`}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <Badge variant="outline" className="font-mono text-xs">
                    {experience.start_date} &ndash;{" "}
                    {experience.is_current ? "Present" : experience.end_date}
                  </Badge>
                  <ConfidenceBadge confidence={experience.confidence} />
                  <EditButton onClick={handleOpen} />
                </div>
              </div>
            </div>
          </div>
        </CardHeader>

        {expanded && experience.bullets.length > 0 && (
          <CardContent className="pt-0 pl-18">
            <Separator className="mb-4" />
            <ul className="flex flex-col gap-3">
              {experience.bullets.map((bullet) => (
                <li key={bullet.id} className="flex flex-col gap-2">
                  <div className="flex items-start gap-3">
                    <span className="mt-2 size-1.5 rounded-full bg-emerald/40 shrink-0" />
                    <p className="text-sm leading-relaxed">{bullet.text}</p>
                  </div>
                  {(bullet.skills.length > 0 ||
                    bullet.metrics.length > 0) && (
                    <div className="flex flex-wrap gap-1.5 ml-4.5">
                      {bullet.skills.map((skill) => (
                        <Badge
                          key={skill}
                          variant="outline"
                          className="text-xs font-mono"
                        >
                          {skill}
                        </Badge>
                      ))}
                      {bullet.metrics.map((metric) => (
                        <Badge
                          key={metric}
                          variant="outline"
                          className="text-xs font-mono border-emerald/25 text-emerald"
                        >
                          <Award className="size-3 mr-0.5" />
                          {metric}
                        </Badge>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        )}
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Experience</DialogTitle>
            <DialogDescription>
              Update role details and bullet points.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Job Title</FieldLabel>
                <Input
                  value={draft.title}
                  onChange={(e) =>
                    setDraft({ ...draft, title: e.target.value })
                  }
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Organization</FieldLabel>
                <Input
                  value={draft.organization}
                  onChange={(e) =>
                    setDraft({ ...draft, organization: e.target.value })
                  }
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Location</FieldLabel>
                <Input
                  value={draft.location ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      location: e.target.value || null,
                    })
                  }
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Start Date</FieldLabel>
                <Input
                  value={draft.start_date}
                  onChange={(e) =>
                    setDraft({ ...draft, start_date: e.target.value })
                  }
                  placeholder="Jan 2023"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>End Date</FieldLabel>
                <Input
                  value={draft.is_current ? "Present" : draft.end_date ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (
                      val.toLowerCase() === "present" ||
                      val.toLowerCase() === "current"
                    ) {
                      setDraft({
                        ...draft,
                        is_current: true,
                        end_date: null,
                      });
                    } else {
                      setDraft({
                        ...draft,
                        is_current: false,
                        end_date: val || null,
                      });
                    }
                  }}
                  placeholder="Present"
                />
              </div>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <FieldLabel>Bullet Points</FieldLabel>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={addBullet}
              >
                <Plus className="size-3.5" data-icon="inline-start" />
                Add Bullet
              </Button>
            </div>

            <div className="flex flex-col gap-2">
              {draft.bullets.map((bullet, idx) => (
                <div key={bullet.id} className="flex gap-2">
                  <Textarea
                    value={bullet.text}
                    onChange={(e) => updateBullet(idx, e.target.value)}
                    rows={2}
                    className="text-sm flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => removeBullet(idx)}
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              className="text-destructive hover:text-destructive"
              onClick={() => {
                onDelete();
                setEditOpen(false);
              }}
            >
              <Trash2 className="size-3.5" data-icon="inline-start" />
              Delete
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Project Card with Edit ─────────────────────────────

function ProjectCard({
  project,
  onSave,
  onDelete,
}: {
  project: Project;
  onSave: (proj: Project) => void;
  onDelete: () => void;
}) {
  const [editOpen, setEditOpen] = useState(false);
  const [draft, setDraft] = useState(project);

  function handleOpen() {
    setDraft(project);
    setEditOpen(true);
  }

  function handleSave() {
    onSave(draft);
    setEditOpen(false);
  }

  function updateBullet(idx: number, text: string) {
    const bullets = [...draft.bullets];
    bullets[idx] = { ...bullets[idx], text };
    setDraft({ ...draft, bullets });
  }

  function removeBullet(idx: number) {
    setDraft({
      ...draft,
      bullets: draft.bullets.filter((_, i) => i !== idx),
    });
  }

  function addBullet() {
    setDraft({
      ...draft,
      bullets: [
        ...draft.bullets,
        {
          id: crypto.randomUUID(),
          text: "",
          skills: [],
          metrics: [],
          evidence_ids: [],
          approved: false,
        },
      ],
    });
  }

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-base">{project.name}</CardTitle>
                {project.description && (
                  <CardDescription className="mt-1">
                    {project.description}
                  </CardDescription>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <ConfidenceBadge confidence={project.confidence} />
                <EditButton onClick={handleOpen} />
              </div>
            </div>
        </CardHeader>
        <CardContent>
          {project.skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {project.skills.map((skill) => (
                <Badge
                  key={skill}
                  variant="outline"
                  className="text-xs font-mono"
                >
                  {skill}
                </Badge>
              ))}
            </div>
          )}
          {project.bullets.length > 0 && (
            <ul className="flex flex-col gap-2.5">
              {project.bullets.map((bullet) => (
                <li
                  key={bullet.id}
                  className="flex items-start gap-3 text-sm text-muted-foreground leading-relaxed"
                >
                  <span className="mt-2 size-1.5 rounded-full bg-muted-foreground/30 shrink-0" />
                  <span>{bullet.text}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
            <DialogDescription>
              Update project name, description, skills, and bullets.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Project Name</FieldLabel>
              <Input
                value={draft.name}
                onChange={(e) =>
                  setDraft({ ...draft, name: e.target.value })
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Description</FieldLabel>
              <Input
                value={draft.description ?? ""}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    description: e.target.value || null,
                  })
                }
                placeholder="One-line project summary"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>URL</FieldLabel>
              <Input
                value={draft.url ?? ""}
                onChange={(e) =>
                  setDraft({ ...draft, url: e.target.value || null })
                }
                placeholder="https://github.com/..."
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Skills</FieldLabel>
              <TagInput
                tags={draft.skills}
                onChange={(skills) => setDraft({ ...draft, skills })}
                placeholder="Type a skill and press Enter"
              />
              <p className="text-xs text-muted-foreground">
                Press Enter or comma to add. Backspace to remove last.
              </p>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <FieldLabel>Bullet Points</FieldLabel>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={addBullet}
              >
                <Plus className="size-3.5" data-icon="inline-start" />
                Add Bullet
              </Button>
            </div>

            <div className="flex flex-col gap-2">
              {draft.bullets.map((bullet, idx) => (
                <div key={bullet.id} className="flex gap-2">
                  <Textarea
                    value={bullet.text}
                    onChange={(e) => updateBullet(idx, e.target.value)}
                    rows={2}
                    className="text-sm flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => removeBullet(idx)}
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              className="text-destructive hover:text-destructive"
              onClick={() => {
                onDelete();
                setEditOpen(false);
              }}
            >
              <Trash2 className="size-3.5" data-icon="inline-start" />
              Delete
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Education Card with Edit ───────────────────────────

function EducationCard({
  education,
  onSave,
  onDelete,
}: {
  education: Education;
  onSave: (edu: Education) => void;
  onDelete: () => void;
}) {
  const [editOpen, setEditOpen] = useState(false);
  const [draft, setDraft] = useState(education);

  function handleOpen() {
    setDraft(education);
    setEditOpen(true);
  }

  function handleSave() {
    onSave(draft);
    setEditOpen(false);
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="flex size-10 items-center justify-center rounded-lg bg-muted/50 ring-1 ring-border shrink-0">
              <GraduationCap className="size-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">
                      {education.degree}
                      {education.field && education.field !== "Unknown"
                        ? ` in ${education.field}`
                        : ""}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {education.institution}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <ConfidenceBadge confidence={education.confidence} />
                    <EditButton onClick={handleOpen} />
                  </div>
                </div>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {(education.start_date || education.end_date) && (
                  <Badge variant="outline" className="font-mono text-xs">
                    {education.start_date && `${education.start_date} – `}
                    {education.end_date ?? "Present"}
                  </Badge>
                )}
                {education.gpa && (
                  <Badge
                    variant="outline"
                    className="font-mono text-xs border-emerald/25 text-emerald"
                  >
                    GPA: {education.gpa}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Education</DialogTitle>
            <DialogDescription>
              Update degree, field, institution, and dates.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <FieldLabel>Institution</FieldLabel>
              <Input
                value={draft.institution}
                onChange={(e) =>
                  setDraft({ ...draft, institution: e.target.value })
                }
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Degree</FieldLabel>
                <Input
                  value={draft.degree}
                  onChange={(e) =>
                    setDraft({ ...draft, degree: e.target.value })
                  }
                  placeholder="BS, MS, PhD..."
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Field of Study</FieldLabel>
                <Input
                  value={draft.field ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      field: e.target.value || null,
                    })
                  }
                  placeholder="Computer Science"
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Start Date</FieldLabel>
                <Input
                  value={draft.start_date ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      start_date: e.target.value || null,
                    })
                  }
                  placeholder="Aug 2019"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>End Date</FieldLabel>
                <Input
                  value={draft.end_date ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      end_date: e.target.value || null,
                    })
                  }
                  placeholder="May 2023"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <FieldLabel>GPA</FieldLabel>
                <Input
                  value={draft.gpa ?? ""}
                  onChange={(e) =>
                    setDraft({ ...draft, gpa: e.target.value || null })
                  }
                  placeholder="3.8"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              className="text-destructive hover:text-destructive"
              onClick={() => {
                onDelete();
                setEditOpen(false);
              }}
            >
              <Trash2 className="size-3.5" data-icon="inline-start" />
              Delete
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Skills Card with Edit ──────────────────────────────

function SkillsCard({
  skills,
  onSave,
}: {
  skills: CanonicalProfile["skills"];
  onSave: (skills: CanonicalProfile["skills"]) => void;
}) {
  const [editOpen, setEditOpen] = useState(false);
  const [draftText, setDraftText] = useState("");

  function handleOpen() {
    setDraftText(
      skills.map((s) => (s.category ? `${s.category}: ${s.name}` : s.name)).join("\n")
    );
    setEditOpen(true);
  }

  function handleSave() {
    const parsed = draftText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const colonIdx = line.indexOf(":");
        if (colonIdx > 0) {
          return {
            name: line.slice(colonIdx + 1).trim(),
            category: line.slice(0, colonIdx).trim(),
            proficiency: null,
            evidence_ids: [],
            approved: false,
          };
        }
        return {
          name: line,
          category: null,
          proficiency: null,
          evidence_ids: [],
          approved: false,
        };
      });
    onSave(parsed);
    setEditOpen(false);
  }

  if (skills.length === 0) {
    return (
      <EmptyState
        icon={Layers}
        title="No skills"
        description="No skills found in your profile."
      />
    );
  }

  const categories = new Map<string, string[]>();
  for (const skill of skills) {
    const cat = skill.category || "Other";
    if (!categories.has(cat)) categories.set(cat, []);
    categories.get(cat)!.push(skill.name);
  }

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60">
              Skills
            </CardTitle>
            <EditButton onClick={handleOpen} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-5">
            {Array.from(categories.entries()).map(([cat, catSkills]) => (
              <div key={cat}>
                <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-2.5">
                  {cat}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {catSkills.map((skill) => (
                    <Badge
                      key={skill}
                      variant="secondary"
                      className="font-mono text-xs"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Skills</DialogTitle>
            <DialogDescription>
              One skill per line. Use &quot;Category: Skill&quot; format to group them.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            rows={12}
            className="font-mono text-sm"
            placeholder={"Languages: Python\nLanguages: TypeScript\nFrameworks: React\nAWS"}
          />
          <DialogFooter>
            <Button onClick={handleSave}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
