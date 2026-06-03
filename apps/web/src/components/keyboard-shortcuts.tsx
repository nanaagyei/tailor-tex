"use client";

import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useKeyboardShortcuts, shortcutGroups } from "@/lib/use-keyboard-shortcuts";
import type { ShortcutGroup } from "@/lib/use-keyboard-shortcuts";

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center justify-center rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] font-mono font-medium text-foreground min-w-[22px]">
      {children}
    </kbd>
  );
}

function ShortcutRow({ shortcut }: { shortcut: ShortcutGroup["shortcuts"][number] }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-muted-foreground">{shortcut.description}</span>
      <span className="flex items-center gap-1">
        {shortcut.keys.map((key, i) =>
          key === "or" ? (
            <span key={i} className="text-xs text-muted-foreground/50 px-0.5">
              or
            </span>
          ) : (
            <Kbd key={i}>{key}</Kbd>
          ),
        )}
      </span>
    </div>
  );
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KeyboardShortcuts({ open, onOpenChange }: Props) {
  const router = useRouter();

  useKeyboardShortcuts([
    {
      keys: ["G", "H"],
      handler: () => router.push("/"),
    },
    {
      keys: ["G", "I"],
      handler: () => router.push("/import"),
    },
    {
      keys: ["G", "P"],
      handler: () => router.push("/profile"),
    },
    {
      keys: ["G", "J"],
      handler: () => router.push("/jobs/new"),
    },
    {
      keys: ["G", "S"],
      handler: () => router.push("/settings"),
    },
  ]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Press{" "}
            <Kbd>?</Kbd> anytime to show this dialog.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          {shortcutGroups.map((group) => (
            <div key={group.name}>
              <h4 className="text-xs font-medium uppercase tracking-widest text-muted-foreground/60 mb-1">
                {group.name}
              </h4>
              <div className="flex flex-col divide-y divide-border">
                {group.shortcuts.map((s, i) => (
                  <ShortcutRow key={i} shortcut={s} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { shortcutGroups };
