import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface StatItem { label: string; value: string | number; hint?: string; tone?: "blue" | "red" | "yellow" | "green" | "violet"; icon?: LucideIcon }

const TONES = ["blue", "red", "yellow", "green", "violet"] as const;

/** KPI "gems": Google-colour gradient tiles that lift and gloss on hover. */
export function Stats({ items }: { items: StatItem[] }) {
  return (
    <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {items.map((it, i) => {
        const Icon = it.icon;
        return (
          <div key={it.label} className={cn("gem lift rounded-2xl p-5", `gem-${it.tone ?? TONES[i % TONES.length]}`)}>
            <dt className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide opacity-90">
              {Icon && <Icon className="size-5" aria-hidden="true" />}{it.label}
            </dt>
            <dd className="mt-2 font-display text-5xl font-semibold leading-none tabular-nums">{it.value}</dd>
            {it.hint && <dd className="mt-1 text-sm opacity-90">{it.hint}</dd>}
          </div>
        );
      })}
    </dl>
  );
}
