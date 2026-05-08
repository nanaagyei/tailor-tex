import Link from "next/link";
import { FileX } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: { label: string; href: string } | React.ReactNode;
}

export function EmptyState({ icon: Icon = FileX, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl bg-muted/50 ring-1 ring-border mb-4">
        <Icon className="size-6 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-medium text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-md mb-6">{description}</p>
      {action && typeof action === "object" && "label" in action && "href" in action ? (
        <Button render={<Link href={(action as { label: string; href: string }).href} />}>
          {(action as { label: string; href: string }).label}
        </Button>
      ) : (
        action
      )}
    </div>
  );
}
