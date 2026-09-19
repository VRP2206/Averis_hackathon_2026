import { cn } from "@/lib/utils";

export interface StatItem { label: string; value: string | number; hint?: string; tone?: "ok" | "bad" | "warn" }

// Compact KPI row; tone adds a coloured value but the label always carries the meaning.
export function Stats({ items }: { items: StatItem[] }) {
  return (
    <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {items.map((it) => (
        <div key={it.label} className="rounded-lg border bg-card p-4">
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{it.label}</dt>
          <dd className={cn("mt-1 text-2xl font-semibold tabular-nums",
            it.tone === "ok" && "text-ok", it.tone === "bad" && "text-bad", it.tone === "warn" && "text-warn")}>
            {it.value}
          </dd>
          {it.hint && <dd className="text-xs text-muted-foreground">{it.hint}</dd>}
        </div>
      ))}
    </dl>
  );
}
