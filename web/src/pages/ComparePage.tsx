import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, ClipboardCopy, Pencil, Route } from "lucide-react";
import { api, FIELD_LABELS, FIELDS, LANGUAGES, REASON_TEXT, type EmailRecord, type EmailResult, type Status, type TranslationResult } from "@/lib/api";
import { Languages } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { CategoryChip, StatusBadge } from "@/components/StatusBadge";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

export function ComparePage() {
  const { id = "" } = useParams();
  const [email, setEmail] = useState<EmailRecord | null>(null);
  const [result, setResult] = useState<EmailResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [overrideOpen, setOverrideOpen] = useState(false);
  const { t } = useT();

  useEffect(() => {
    setError(null);
    api.email(id).then(setEmail).catch((e) => setError(e.message));
    api.result(id).then(setResult).catch(async () => {
      try { setResult(await api.processOne(id)); } catch (e) { setError((e as Error).message); }
    });
  }, [id]);

  async function approve() {
    if (!result) return;
    const r = await api.review(id, { status: result.status, defect_fields: result.defect_fields, reviewer: reviewerName() });
    setResult(r); setNotice("Result approved and recorded.");
  }
  async function copyDraft() {
    if (!result?.draft_reply) return;
    await navigator.clipboard.writeText(result.draft_reply);
    setNotice("Draft reply copied to clipboard.");
  }

  if (error) return <p role="alert" className="text-bad">{error}</p>;
  if (!email || !result) return <p aria-live="polite">Loading…</p>;

  const si = result.extractions.find((e) => e.doc_type === "SI");
  const bl = result.extractions.find((e) => e.doc_type === "BL");

  return (
    <div className="space-y-6">
      <p className="sr-only" aria-live="polite">{notice}</p>
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:underline"><ArrowLeft className="size-4" aria-hidden="true" />{t("compare.back")}</Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold leading-tight">{email.subject || "(no subject)"}</h1>
          <p className="text-sm text-muted-foreground">{email.email_id} · from {email.from}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <CategoryChip category={result.category} />
            {result.category === "BL_COMPARISON" && <StatusBadge status={result.status} />}
            <span className="text-xs text-muted-foreground">decided by {result.decided_by}
              {result.classification && ` · confidence ${(result.classification.confidence * 100).toFixed(0)}%`}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={approve}><Check className="size-4" aria-hidden="true" />{t("compare.approve")}</Button>
          <Button variant="outline" onClick={() => setOverrideOpen(true)}><Pencil className="size-4" aria-hidden="true" />{t("compare.override")}</Button>
          {result.draft_reply && <Button onClick={copyDraft}><ClipboardCopy className="size-4" aria-hidden="true" />{t("compare.copy")}</Button>}
          <Button asChild variant="outline"><Link to={`/emails/${id}/why`}><Route className="size-4" aria-hidden="true" />{t("why.open")}</Link></Button>
        </div>
      </div>

      {result.status === "NEEDS_REVIEW" && result.review_reason && (
        <div role="status" className="rounded-md border border-warn bg-warn-bg p-3 text-sm text-warn">
          <strong>Needs human review: {result.review_reason.replace("_", " ")}.</strong> {REASON_TEXT[result.review_reason]}
          {result.notes.length > 0 && <ul className="mt-1 list-disc pl-5">{result.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <Card>
          <CardHeader><CardTitle className="text-base">{t("compare.email")}</CardTitle></CardHeader>
          <CardContent>
            <TranslatePanel emailId={id} />
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap text-sm">{email.body}</pre>
            {email.attachments.length > 0 && (
              <ul className="mt-3 space-y-1 text-xs text-muted-foreground" aria-label="Attachments">
                {email.attachments.map((a) => <li key={a}>{a.split("/").pop()}</li>)}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">{t("compare.table")}</CardTitle></CardHeader>
          <CardContent>
            {result.comparisons.length === 0 && !si ? (
              <p className="text-sm text-muted-foreground">No comparison was made for this email.</p>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <caption className="sr-only">Field-by-field comparison; mismatched rows are marked</caption>
                  <TableHeader><TableRow>
                    <TableHead scope="col">{t("compare.field")}</TableHead><TableHead scope="col">{t("compare.si")}</TableHead><TableHead scope="col">{t("compare.bl")}</TableHead><TableHead scope="col">{t("compare.result")}</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {FIELDS.map((f) => {
                      const c = result.comparisons.find((x) => x.field === f);
                      const sv = si?.fields[f]; const bv = bl?.fields[f];
                      const bad = c ? !c.match : false;
                      const missing = !c && (sv && !sv.value || bv && !bv.value || sv?.blank || bv?.blank);
                      return (
                        <TableRow key={f} className={cn(bad && "bg-bad-bg/60", missing && "bg-warn-bg/60")}>
                          <TableHead scope="row" className="font-medium">{FIELD_LABELS[f]}</TableHead>
                          <TableCell className="max-w-56 whitespace-normal break-words"><Evidence value={sv?.value ?? c?.si_value ?? null} source={sv?.source} blank={sv?.blank} /></TableCell>
                          <TableCell className="max-w-56 whitespace-normal break-words"><Evidence value={bv?.value ?? c?.bl_value ?? null} source={bv?.source} blank={bv?.blank} /></TableCell>
                          <TableCell className="text-xs font-semibold">
                            {c ? (c.match ? <span className="text-ok">{t("compare.match")}</span> : <span className="text-bad">{t("compare.mismatch")}</span>) : missing ? <span className="text-warn">{t("compare.missing")}</span> : "—"}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
                <p className="mt-2 text-xs text-muted-foreground">{t("compare.hover")}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {result.draft_reply && (
        <Card>
          <CardHeader><CardTitle className="text-base">{t("compare.draft")}</CardTitle></CardHeader>
          <CardContent><pre className="whitespace-pre-wrap text-sm">{result.draft_reply}</pre></CardContent>
        </Card>
      )}

      <OverrideDialog open={overrideOpen} onOpenChange={setOverrideOpen} result={result}
        onSaved={(r) => { setResult(r); setNotice("Override saved."); }} />
    </div>
  );
}

function TranslatePanel({ emailId }: { emailId: string }) {
  const [target, setTarget] = useState(() => { try { return localStorage.getItem("sdoc.lang") || "en"; } catch { return "en"; } });
  const [busy, setBusy] = useState(false);
  const [t, setT] = useState<TranslationResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const { t: tr } = useT();

  useEffect(() => { setT(null); setErr(null); }, [emailId]);

  async function run() {
    setBusy(true); setErr(null);
    try { localStorage.setItem("sdoc.lang", target); } catch { /* ignore */ }
    try { setT(await api.translate(emailId, target)); } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <div className="mb-3 space-y-2">
      <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); run(); }}>
        <div>
          <Label htmlFor="lang">{tr("compare.translateTo")}</Label>
          <select id="lang" className="w-full" value={target} onChange={(e) => setTarget(e.target.value)}>
            {LANGUAGES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
        </div>
        <Button type="submit" variant="outline" size="sm" disabled={busy}>
          <Languages className="size-4" aria-hidden="true" />{busy ? tr("compare.translating") : tr("compare.translate")}
        </Button>
      </form>
      {err && <p role="alert" className="text-xs text-bad">{err}</p>}
      {t && (
        <div role="status" className="rounded-md border bg-accent/40 p-3 text-sm">
          <p className="mb-1 text-xs text-muted-foreground">
            Detected language: <strong>{t.source_language}</strong>.{" "}
            {t.translated ? `Translated to ${t.target_language} by the AI model (${t.llm_provider}); check names and numbers against the original.` : t.note}
          </p>
          {t.translated && <pre className="max-h-72 overflow-auto whitespace-pre-wrap">{t.text}</pre>}
        </div>
      )}
    </div>
  );
}

function Evidence({ value, source, blank }: { value: string | null; source?: string | null; blank?: boolean }) {
  if (value == null) return <span className="text-xs text-muted-foreground">not found</span>;
  const text = blank ? `${value || "(blank)"} ` : value;
  if (!source) return <span className="text-sm">{text}</span>;
  return (
    <Tooltip>
      <TooltipTrigger asChild><button type="button" className="rounded text-left text-sm whitespace-normal underline decoration-dotted underline-offset-2">{text}</button></TooltipTrigger>
      <TooltipContent className="max-w-sm font-mono text-xs">{source}</TooltipContent>
    </Tooltip>
  );
}

function reviewerName() {
  try { return localStorage.getItem("sdoc.reviewer") || "reviewer"; } catch { return "reviewer"; }
}

function OverrideDialog({ open, onOpenChange, result, onSaved }:
  { open: boolean; onOpenChange: (o: boolean) => void; result: EmailResult; onSaved: (r: EmailResult) => void }) {
  const [status, setStatus] = useState<Status>(result.status);
  const [fields, setFields] = useState<string[]>(result.defect_fields);
  const [reviewer, setReviewer] = useState(reviewerName());
  const [consent, setConsent] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { setStatus(result.status); setFields(result.defect_fields); }, [result]);

  async function save(e: React.FormEvent) {
    e.preventDefault(); setErr(null); setSaving(true);
    try {
      try { localStorage.setItem("sdoc.reviewer", reviewer); } catch { /* ignore */ }
      onSaved(await api.review(result.email_id, { status, defect_fields: status === "MISMATCH" ? fields : [], reviewer: reviewer || "reviewer" }));
      onOpenChange(false);
    } catch (ex) { setErr((ex as Error).message); } finally { setSaving(false); }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={save} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Override result</DialogTitle>
            <DialogDescription>Your decision replaces the system's and is recorded in the audit trail.</DialogDescription>
          </DialogHeader>
          <div>
            <Label htmlFor="ov-status">Status</Label>
            <select id="ov-status" className="w-full" value={status} onChange={(e) => setStatus(e.target.value as Status)}>
              <option value="OK">OK</option><option value="MISMATCH">Mismatch</option><option value="NEEDS_REVIEW">Needs review</option>
            </select>
          </div>
          {status === "MISMATCH" && (
            <fieldset>
              <legend className="text-sm font-medium">Fields that differ</legend>
              <div className="mt-1 grid grid-cols-2 gap-1">
                {FIELDS.map((f) => (
                  <label key={f} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" className="size-4" checked={fields.includes(f)}
                      onChange={(e) => setFields((cur) => e.target.checked ? [...cur, f] : cur.filter((x) => x !== f))} />
                    {FIELD_LABELS[f]}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          <div>
            <Label htmlFor="reviewer">Your name (optional)</Label>
            <Input id="reviewer" value={reviewer} onChange={(e) => setReviewer(e.target.value)} autoComplete="name" />
            <p className="mt-1 text-xs text-muted-foreground">Stored with this decision so the team can see who approved it. Leave as "reviewer" to stay anonymous. See our <Link className="underline" to="/privacy">privacy policy</Link>.</p>
          </div>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" className="mt-1 size-4 shrink-0" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
            <span>I understand this decision and my name will be recorded in the audit trail.</span>
          </label>
          {err && <p role="alert" className="text-sm text-bad">{err}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving || !consent}>{saving ? "Saving…" : "Save override"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
