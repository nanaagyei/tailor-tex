import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type ValidationStatus = "supported" | "needs_confirmation" | "rejected";

const statusConfig: Record<ValidationStatus, { label: string; className: string }> = {
  supported: {
    label: "Supported",
    className: "bg-emerald/15 text-emerald border-emerald/25",
  },
  needs_confirmation: {
    label: "Needs Confirmation",
    className: "bg-warning/15 text-warning border-warning/25",
  },
  rejected: {
    label: "Rejected",
    className: "bg-destructive/15 text-destructive border-destructive/25",
  },
};

interface ValidationBadgeProps {
  status: ValidationStatus;
  className?: string;
}

export function ValidationBadge({ status, className }: ValidationBadgeProps) {
  const config = statusConfig[status];
  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  );
}
