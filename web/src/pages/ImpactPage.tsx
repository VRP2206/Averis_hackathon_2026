import { useEffect, useMemo, useState } from "react";
import { api, type EmailResult, type Metrics } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Stats } from "@/components/Stats";
import { useT } from "@/lib/i18n";
import { measured } from "@/content/results";

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

export function ImpactPage() {
  const [m, setM] = useState<Metrics | null>(null);
  const [results, setResults] = useState<EmailResult[]>([]);
  const [noTruth, setNoTruth] = useState(false);
  const { t } = useT();

  useEffect(() => {
    api.metrics().then(setM).catch(() => setNoTruth(true));
    api.results().then(setResults).catch(() => undefined);
  }, []);

  const ops = useMemo(() => {
    const bl = results.filter((r) => r.category === "BL_COMPARISON");
    const by = (k: string) => results.filter((r) => r.decided_by === k).length;
    return {
      total: results.length,
      auto: bl.filter((r) => r.status !== "NEEDS_REVIEW").length,
      escalated: bl.filter((r) => r.status === "NEEDS_REVIEW").length,
      mismatches: bl.filter((r) => r.status === "MISMATCH").length,
      rule: by("rule"), llm: by("llm"), human: by("human"),
      minutesSaved: bl.length * 4, // assumption: ~4 min per manual 7-field check; state it as an assumption
    };
  }, [results]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="hover-sheen inline-block">{t("impact.title")}</h1>
        <p className="text-sm text-muted-foreground">Computed live from the API. Accuracy figures are measured on the hackathon dataset provided by the organisers (synthetic), not on production mail.</p>
      </div>

      <section aria-labelledby="ops">
        <h2 id="ops" className="mb-2 text-sm font-medium text-muted-foreground">Operations</h2>
        <Stats items={[
          { label: "Emails processed", value: ops.total },
          { label: "Checks auto-completed", value: ops.auto, tone: "green" },
          { label: "Escalated to a person", value: ops.escalated, tone: "yellow" },
          { label: "Mismatches found", value: ops.mismatches, tone: "red" },
        ]} />
        <p className="mt-2 text-xs text-muted-foreground">
          Decisions by rule {ops.rule} · by AI model {ops.llm} · by human {ops.human}. Estimated reviewer time saved ≈ {ops.minutesSaved} min, assuming 4 min per manual check (assumption, not measured).
        </p>
      </section>

      <section aria-labelledby="acc">
        <h2 id="acc" className="mb-2 text-sm font-medium text-muted-foreground">Accuracy vs answer key</h2>
        {noTruth && (
          <>
            <p className="mb-3 text-muted-foreground">
              The organisers' answer key is deliberately not deployed to this server, so these figures were measured
              on {measured.dataset} by running the same pipeline against that key on {measured.asOf}.
              Reproduce them with <code>{measured.command}</code>.
            </p>
            <Stats items={[
              { label: "Final score", value: measured.finalScore, hint: "organisers' formula", tone: "blue" },
              { label: "Classification accuracy", value: measured.classificationAccuracy, hint: "5 categories", tone: "red" },
              { label: "Defects fully caught", value: measured.defectsCaught, hint: "exact fields, end-to-end", tone: "yellow" },
              { label: "False alarms", value: measured.falseAlarms, hint: "clean pairs flagged", tone: "green" },
            ]} />
            <p className="mt-2 text-sm text-muted-foreground">
              Escalations caught with the right reason: {measured.escalations}. {measured.tests} automated tests pass.
              Measured offline, not a claim about production mail.
            </p>
          </>
        )}
        {m && (
          <>
            <Stats items={[
              { label: "Final score", value: m.final_score.toFixed(3), hint: "organisers' formula" },
              { label: "Classification accuracy", value: pct(m.stage1.accuracy) },
              { label: "Defects fully caught", value: `${m.end_to_end.success}/${m.end_to_end.total}`, hint: "exact fields, end-to-end" },
              { label: "False-alarm rate", value: pct(1 - m.stage3.defect_precision), hint: "clean pairs flagged" },
            ]} />
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-base">Per-category F1</CardTitle></CardHeader>
                <CardContent>
                  <table className="w-full text-sm"><caption className="sr-only">F1 per category</caption>
                    <tbody>{Object.entries(m.stage1.per_category).map(([c, v]) => (
                      <tr key={c} className="border-b last:border-0"><th scope="row" className="py-1 text-left font-normal">{c.replaceAll("_", " ")}</th><td className="py-1 text-right tabular-nums">{v.f1.toFixed(3)}</td></tr>
                    ))}</tbody>
                  </table>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-base">Escalation quality</CardTitle></CardHeader>
                <CardContent className="text-sm">
                  <p>Recall {pct(m.reliability.escalation_recall)} · precision {pct(m.reliability.escalation_precision)}</p>
                  <p className="text-muted-foreground">{m.reliability.pred_review} escalated, {m.reliability.gold_review} genuinely needed review.</p>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
