import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, FileSearch, Info, ListChecks, Scale, ScanText, ShieldCheck, Tags, XCircle, type LucideIcon } from "lucide-react";
import { api, type EmailRecord, type EmailResult, type TraceStep } from "@/lib/api";
import { useT, type Key } from "@/lib/i18n";
import { CategoryChip, StatusBadge } from "@/components/StatusBadge";
import { cn } from "@/lib/utils";

const STAGE: Record<TraceStep["stage"], { icon: LucideIcon; ring: string }> = {
  classify: { icon: Tags, ring: "bg-g-blue" },
  read: { icon: FileSearch, ring: "bg-primary" },
  gate: { icon: ShieldCheck, ring: "bg-g-yellow" },
  extract: { icon: ScanText, ring: "bg-g-blue" },
  compare: { icon: Scale, ring: "bg-g-green" },
  decide: { icon: ListChecks, ring: "bg-g-red" },
};

/** Audit trail for one email: each pipeline step, its outcome and the exact text it used. */
export function WhyPage() {
  const { id = "" } = useParams();
  const { t } = useT();
  const [email, setEmail] = useState<EmailRecord | null>(null);
  const [result, setResult] = useState<EmailResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.email(id).then(setEmail).catch((e) => setError(e.message));
    // Use the stored result; only re-run if it predates tracing (never over a human override).
    api.result(id)
      .then((r) => (r.trace?.length || r.decided_by === "human" ? r : api.processOne(id)))
      .catch(() => api.processOne(id))
      .then(setResult)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p role="alert" className="text-bad">{error}</p>;
  if (!email || !result) return <p aria-live="polite">…</p>;

  return (
    <div className="space-y-8">
      <Link to={`/emails/${id}`} className="inline-flex items-center gap-1 text-muted-foreground hover:underline">
        <ArrowLeft className="size-4" aria-hidden="true" />{t("why.back")}
      </Link>

      <header className="space-y-3">
        <h1 className="hover-sheen inline-block">{t("why.title")}</h1>
        <p className="text-lg text-muted-foreground">{t("why.subtitle")}</p>
        <div className="lift-soft flex flex-wrap items-center gap-3 rounded-2xl border-l-8 border-l-g-blue bg-card p-4">
          <span className="min-w-0 flex-1 truncate font-semibold" title={email.subject}>{email.subject}</span>
          <CategoryChip category={result.category} />
          {result.category === "BL_COMPARISON" && <StatusBadge status={result.status} />}
          <span className="text-sm text-muted-foreground">{result.trace.length} {t("why.steps")}</span>
        </div>
      </header>

      <ol className="relative space-y-5 border-l-4 border-dashed border-border pl-8">
        {result.trace.map((s, i) => <Step key={i} step={s} n={i + 1} />)}
      </ol>
    </div>
  );
}

function Step({ step, n }: { step: TraceStep; n: number }) {
  const { t } = useT();
  const { icon: Icon, ring } = STAGE[step.stage] ?? STAGE.decide;
  const Outcome = step.outcome === "pass" ? CheckCircle2 : step.outcome === "fail" ? XCircle : Info;
  return (
    <li className="relative">
      <span className={cn("absolute -left-[3.05rem] top-3 flex size-10 items-center justify-center rounded-full text-white shadow-md", ring)} aria-hidden="true">
        <Icon className="size-5" />
      </span>
      <article className={cn("lift-soft rounded-2xl border bg-card p-5",
        step.outcome === "fail" && "border-l-8 border-l-g-red",
        step.outcome === "decision" && "border-l-8 border-l-primary")}>
        <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
          {n}. {t(`stage.${step.stage}` as Key)}
        </p>
        <h2 className="mt-1 flex items-center gap-2 text-xl">
          {step.outcome !== "info" && step.outcome !== "decision" && (
            <Outcome className={cn("size-5 shrink-0", step.outcome === "pass" ? "text-ok" : "text-bad")} aria-hidden="true" />
          )}
          <span>{step.title}</span>
          {step.outcome === "pass" && <span className="sr-only">passed</span>}
          {step.outcome === "fail" && <span className="sr-only">failed</span>}
        </h2>
        {step.detail && <p className="mt-1 text-muted-foreground">{step.detail}</p>}
        {step.evidence.length > 0 && (
          <ul className="mt-3 space-y-1 overflow-x-auto rounded-xl bg-muted p-3 font-mono text-sm">
            {step.evidence.map((e, i) => (
              <li key={i} className={cn("whitespace-pre-wrap break-words",
                e.startsWith("MISMATCH") && "font-bold text-bad", e.startsWith("MATCH") && "text-ok")}>{e}</li>
            ))}
          </ul>
        )}
      </article>
    </li>
  );
}
