"use client";

import { useState, useCallback } from "react";
import { SidebarNav } from "./sidebar-nav";
import { MobileNav } from "./mobile-nav";
import { KeyboardShortcuts } from "@/components/keyboard-shortcuts";
import { useKeyboardShortcuts } from "@/lib/use-keyboard-shortcuts";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  const openShortcuts = useCallback(() => setShortcutsOpen(true), []);
  const closeShortcuts = useCallback(() => setShortcutsOpen(false), []);

  useKeyboardShortcuts([
    {
      keys: ["?"],
      handler: () => setShortcutsOpen((prev) => !prev),
    },
    {
      keys: ["Cmd", "K"],
      handler: openShortcuts,
    },
    {
      keys: ["Ctrl", "K"],
      handler: openShortcuts,
    },
    {
      keys: ["Escape"],
      handler: () => {
        if (shortcutsOpen) {
          setShortcutsOpen(false);
        }
      },
    },
  ]);

  return (
    <div className="flex min-h-dvh flex-col md:flex-row">
      <MobileNav />
      <SidebarNav />
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
      <KeyboardShortcuts open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
    </div>
  );
}
