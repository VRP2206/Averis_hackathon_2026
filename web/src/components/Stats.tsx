import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

export interface StatItem {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "blue" | "red" | "yellow" | "green" | "violet";
  icon?: LucideIcon;
  onClick?: () => void;      // when set, the tile is a button (e.g. "show me these")
  active?: boolean;
}

const TONES = ["blue", "red", "yellow", "green", "violet"] as const;

/** KPI "gems": Google-colour gradient tiles that lift and gloss on hover.
 *  Clickable tiles render as real buttons so keyboard users get them too. */
export function Stats({ items }: { items: StatItem[] }) {
  const { t } = useT();
  return (
    <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {items.map((it, i) => {
        const Icon = it.icon;
        const cls = cn("gem lift w-full rounded-2xl p-5 text-left", `gem-${it.tone ?? TONES[i % TONES.length]}`,
          it.onClick && "cursor-pointer focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-ring",
          it.active && "ring-4 ring-white/80 ring-offset-2 ring-offset-background");
        const body = (
          <>
            <dt className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide opacity-90">
              {Icon && <Icon className="size-5" aria-hidden="true" />}{it.label}
            </dt>
            <dd className="mt-2 font-display text-5xl font-semibold leading-none tabular-nums">{it.value}</dd>
            <dd className="mt-1 text-sm opacity-90">{it.hint ?? (it.onClick ? (it.active ? t("tile.showing") : t("tile.click")) : "")}</dd>
          </>
        );
        return it.onClick ? (
          <button key={it.label} type="button" onClick={it.onClick} aria-pressed={it.active} className={cls}>{body}</button>
        ) : (
          <div key={it.label} className={cls}>{body}</div>
        );
      })}
    </dl>
  );
}
