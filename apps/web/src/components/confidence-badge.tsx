import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ConfidenceBadgeProps {
  confidence?: number;
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  if (confidence === undefined) {
    return (
      <Badge variant="outline" className="text-xs font-mono border-muted-foreground/30 text-muted-foreground">
        Manual
      </Badge>
    );
  }

  const pct = Math.round(confidence * 100);
  const label = pct >= 80 ? "High" : pct >= 50 ? "Medium" : "Low";
  const colorClass =
    pct >= 80
      ? "border-emerald/25 text-emerald"
      : pct >= 50
        ? "border-warning/25 text-warning"
        : "border-destructive/25 text-destructive";

  return (
    <Badge variant="outline" className={cn("text-xs font-mono", colorClass)}>
      {label} {pct}%
    </Badge>
  );
}
