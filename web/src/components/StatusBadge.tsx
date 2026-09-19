import { AlertTriangle, CheckCircle2, XCircle, type LucideIcon } from "lucide-react";
import type { Status } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

// Status is always conveyed by text + icon, never colour alone (WCAG 1.4.1).
const STYLES: Record<Status, { label: string; icon: LucideIcon; className: string }> = {
  OK: { label: "OK", icon: CheckCircle2, className: "bg-ok-bg text-ok" },
  MISMATCH: { label: "Mismatch", icon: XCircle, className: "bg-bad-bg text-bad" },
  NEEDS_REVIEW: { label: "Needs review", icon: AlertTriangle, className: "bg-warn-bg text-warn" },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const s = STYLES[status];
  const Icon = s.icon;
  const { t } = useT();
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold", s.className, className)}>
      <Icon className="size-3.5" aria-hidden="true" />
      {t(`status.${status}` as const)}
    </span>
  );
}

const CATEGORY_LABEL: Record<string, string> = {
  BL_COMPARISON: "BL comparison",
  SI_REQUEST: "SI request",
  INVOICE_QUERY: "Invoice query",
  GENERAL: "General",
  SPAM: "Spam",
};

export function CategoryChip({ category }: { category: string }) {
  const { t } = useT();
  const key = `cat.${category}` as Parameters<typeof t>[0];
  return (
    <span className="inline-flex rounded-md border px-2 py-0.5 text-xs text-muted-foreground">
      {category in CATEGORY_LABEL ? t(key) : category}
    </span>
  );
}
