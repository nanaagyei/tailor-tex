"use client";

import { useEffect } from "react";

export interface ShortcutGroup {
  name: string;
  shortcuts: { keys: string[]; description: string }[];
}

export const shortcutGroups: ShortcutGroup[] = [
  {
    name: "Navigation",
    shortcuts: [
      { keys: ["G", "H"], description: "Go to Welcome" },
      { keys: ["G", "I"], description: "Go to Import" },
      { keys: ["G", "P"], description: "Go to Profile" },
      { keys: ["G", "J"], description: "Go to New Job" },
      { keys: ["G", "S"], description: "Go to Settings" },
    ],
  },
  {
    name: "General",
    shortcuts: [
      { keys: ["?", "or", "Ctrl", "K"], description: "Show shortcuts" },
      { keys: ["Esc"], description: "Close dialog" },
    ],
  },
];

export function useKeyboardShortcuts(
  shortcuts: {
    keys: string[];
    handler: () => void;
    ignoreInputs?: boolean;
  }[],
) {
  useEffect(() => {
    let sequence: string[] = [];

    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      for (const shortcut of shortcuts) {
        const modifier = shortcut.keys.some((k) => k === "Cmd" || k === "Ctrl");
        const mainKey = shortcut.keys.find(
          (k) => k !== "Cmd" && k !== "Ctrl" && k !== "G" && k !== "or",
        );

        if (
          mainKey &&
          shortcut.keys.includes("G") &&
          shortcut.keys.length > 1
        ) {
          if (e.key === "g") {
            sequence.push("g");
            setTimeout(() => {
              sequence = [];
            }, 800);
            return;
          }

          if (
            sequence.length === 1 &&
            sequence[0] === "g" &&
            e.key.toLowerCase() === mainKey.toLowerCase()
          ) {
            e.preventDefault();
            sequence = [];
            shortcut.handler();
            return;
          }
          continue;
        }

        if (modifier && (e.metaKey || e.ctrlKey) && mainKey) {
          if (e.key.toLowerCase() === mainKey.toLowerCase()) {
            e.preventDefault();
            shortcut.handler();
            return;
          }
          continue;
        }

        if (
          !modifier &&
          mainKey &&
          shortcut.keys.length === 1 &&
          e.key === mainKey &&
          !e.metaKey &&
          !e.ctrlKey
        ) {
          e.preventDefault();
          shortcut.handler();
          return;
        }
      }

      if (e.key !== "g") {
        sequence = [];
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts]);
}
