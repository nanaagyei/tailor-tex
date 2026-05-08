"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  FileText,
  Upload,
  User,
  Briefcase,
  LayoutDashboard,
  Settings,
  Menu,
  X,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

const navItems = [
  { href: "/", label: "Welcome", icon: LayoutDashboard },
  { href: "/import", label: "Import", icon: Upload },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/jobs/new", label: "New Job", icon: Briefcase },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="md:hidden flex items-center justify-between border-b border-border px-4 py-3 bg-card/50">
      <div className="flex items-center gap-2.5">
        <div className="flex size-7 items-center justify-center rounded-lg bg-emerald/10">
          <FileText className="size-3.5 text-emerald" />
        </div>
        <span className="font-semibold tracking-tight text-sm">TailorTex</span>
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger render={<Button variant="ghost" size="icon" aria-label="Open navigation" />}>
          {open ? <X className="size-5" /> : <Menu className="size-5" />}
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
            <div className="flex size-8 items-center justify-center rounded-lg bg-emerald/10">
              <FileText className="size-4 text-emerald" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold tracking-tight text-sm">TailorTex</span>
              <span className="text-[10px] text-muted-foreground">Local-first</span>
            </div>
          </div>
          <nav className="flex flex-col gap-0.5 p-2">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-emerald/10 text-emerald"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  <item.icon className={cn("size-4", isActive && "text-emerald")} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-border">
            <div className="flex items-center gap-2 rounded-lg bg-emerald/5 border border-emerald/10 px-3 py-2.5">
              <Shield className="size-3.5 text-emerald" />
              <span className="text-xs text-muted-foreground">Local-first mode</span>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
