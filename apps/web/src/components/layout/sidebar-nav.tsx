"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Upload,
  User,
  Briefcase,
  LayoutDashboard,
  Settings,
  Shield,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Welcome", icon: LayoutDashboard },
  { href: "/import", label: "Import", icon: Upload },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/jobs/new", label: "New Job", icon: Briefcase },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function SidebarNav() {
  const pathname = usePathname();
  const isAppRoute = pathname.startsWith("/applications");

  return (
    <aside className="hidden md:flex md:w-56 lg:w-64 flex-col border-r border-border bg-card/50">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <Image
          src="/logo.png"
          alt="TailorTex logo"
          width={36}
          height={36}
          priority
          className="size-9 rounded-lg"
        />
        <div className="flex flex-col">
          <span className="font-semibold tracking-tight text-foreground text-sm">
            TailorTex
          </span>
          <span className="text-[10px] text-muted-foreground leading-none">
            Local-first
          </span>
        </div>
      </div>

      <div className="px-3 mb-1">
        <div className="h-px bg-border" />
      </div>

      <nav className="flex flex-col gap-0.5 p-2 flex-1">
        <p className="px-3 pt-2 pb-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">
          Menu
        </p>
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
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

        {isAppRoute && (
          <>
            <p className="px-3 pt-4 pb-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">
              Active
            </p>
            <Link
              href={pathname}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium bg-emerald/10 text-emerald"
            >
              <FolderOpen className="size-4" />
              Application
            </Link>
          </>
        )}
      </nav>

      <div className="p-3">
        <div className="flex items-center gap-2 rounded-lg bg-emerald/5 border border-emerald/10 px-3 py-2.5">
          <Shield className="size-3.5 text-emerald" />
          <div className="flex flex-col">
            <span className="text-xs font-medium text-foreground">
              Local-first mode
            </span>
            <span className="text-[10px] text-muted-foreground">
              All data stays on your machine
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
