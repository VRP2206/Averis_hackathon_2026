import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Paperclip, RefreshCw } from "lucide-react";
import { api, type Category, type EmailSummary, type Status } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CategoryChip, StatusBadge } from "@/components/StatusBadge";
import { Stats } from "@/components/Stats";

const CATEGORIES: Array<Category | "ALL"> = ["ALL", "BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"];
const STATUSES: Array<Status | "ALL"> = ["ALL", "OK", "MISMATCH", "NEEDS_REVIEW"];

export function InboxPage() {
  const [rows, setRows] = useState<EmailSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<Category | "ALL">("ALL");
  const [status, setStatus] = useState<Status | "ALL">("ALL");
  const [announce, setAnnounce] = useState("");

  const load = () => api.emails().then(setRows).catch((e) => setError(String(e.message)));
  useEffect(() => { load(); }, []);

  const processed = useMemo(() => (rows ?? []).filter((r) => r.result.status || r.result.category).length, [rows]);
  const filtered = useMemo(() => (rows ?? []).filter((r) =>
    (cat === "ALL" || r.result.category === cat) &&
    (status === "ALL" || r.result.status === status) &&
    (!q || `${r.subject} ${r.from} ${r.email_id}`.toLowerCase().includes(q.toLowerCase()))), [rows, cat, status, q]);

  const counts = useMemo(() => {
    const c = { total: rows?.length ?? 0, mismatch: 0, review: 0, ok: 0 };
    for (const r of rows ?? []) {
      if (r.result.status === "MISMATCH") c.mismatch++;
      else if (r.result.status === "NEEDS_REVIEW") c.review++;
      else if (r.result.category === "BL_COMPARISON") c.ok++;
    }
    return c;
  }, [rows]);

  async function processInbox() {
    setBusy(true); setAnnounce("Processing inbox…");
    try {
      const r = await api.processAll();
      setAnnounce(`Processed ${r.processed} emails.`);
      await load();
    } catch (e) { setError(String((e as Error).message)); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Inbox</h1>
          <p className="text-sm text-muted-foreground">Every email triaged; document checks flagged for review.</p>
        </div>
        <Button onClick={processInbox} disabled={busy}>
          <RefreshCw className={busy ? "size-4 animate-spin" : "size-4"} aria-hidden="true" />
          {busy ? "Processing…" : "Process inbox"}
        </Button>
      </div>
      <p className="sr-only" aria-live="polite">{announce}</p>

      <Stats items={[
        { label: "Emails", value: counts.total },
        { label: "Mismatches to amend", value: counts.mismatch, tone: "bad" },
        { label: "Need human review", value: counts.review, tone: "warn" },
        { label: "Checked clean", value: counts.ok, tone: "ok" },
      ]} />

      <form className="grid gap-3 sm:grid-cols-[1fr_auto_auto]" onSubmit={(e) => e.preventDefault()} aria-label="Filter inbox">
        <div>
          <Label htmlFor="search">Search</Label>
          <Input id="search" placeholder="Subject, sender or id" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="cat">Category</Label>
          <select id="cat" className="flex h-9 w-full rounded-md border bg-transparent px-3 text-sm" value={cat} onChange={(e) => setCat(e.target.value as Category | "ALL")}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c === "ALL" ? "All categories" : c.replace("_", " ")}</option>)}
          </select>
        </div>
        <div>
          <Label htmlFor="status">Status</Label>
          <select id="status" className="flex h-9 w-full rounded-md border bg-transparent px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value as Status | "ALL")}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === "ALL" ? "All statuses" : s.replace("_", " ")}</option>)}
          </select>
        </div>
      </form>

      {error && <p role="alert" className="rounded-md border border-bad bg-bad-bg p-3 text-sm text-bad">Could not reach the API: {error}. Is <code>sdoc serve</code> running?</p>}
      {rows && processed === 0 && !error && (
        <p className="rounded-md border p-3 text-sm">No results yet. Choose <strong>Process inbox</strong> to run the pipeline.</p>
      )}

      <div className="overflow-x-auto rounded-md border">
        <Table>
          <caption className="sr-only">Inbox, {filtered.length} of {rows?.length ?? 0} emails shown</caption>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Email</TableHead>
              <TableHead scope="col">From</TableHead>
              <TableHead scope="col">Category</TableHead>
              <TableHead scope="col">Status</TableHead>
              <TableHead scope="col">Fields</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((r) => (
              <TableRow key={r.email_id}>
                <TableCell className="max-w-md">
                  <Link to={`/emails/${r.email_id}`} title={r.subject}
                    className="block truncate font-medium underline-offset-2 hover:underline focus-visible:underline">
                    {r.subject || "(no subject)"}
                  </Link>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{r.email_id}</span>
                    {r.attachments.length > 0 && <span className="inline-flex items-center gap-0.5"><Paperclip className="size-3" aria-hidden="true" />{r.attachments.length} <span className="sr-only">attachments</span></span>}
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{r.from}</TableCell>
                <TableCell><CategoryChip category={r.result.category} /></TableCell>
                <TableCell>{r.result.category === "BL_COMPARISON" ? <StatusBadge status={r.result.status} /> : <span className="text-xs text-muted-foreground">—</span>}</TableCell>
                <TableCell className="text-xs">{r.result.defect_fields.join(", ")}</TableCell>
              </TableRow>
            ))}
            {rows && filtered.length === 0 && (
              <TableRow><TableCell colSpan={5} className="py-10 text-center text-sm text-muted-foreground">No emails match these filters.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
