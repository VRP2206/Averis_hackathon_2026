import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Eraser, Mail, Paperclip, RefreshCw, XCircle } from "lucide-react";
import { api, type Category, type EmailSummary, type Status } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CategoryChip, StatusBadge } from "@/components/StatusBadge";
import { Stats } from "@/components/Stats";
import { MailSources } from "@/components/MailSources";
import { useT, type Key } from "@/lib/i18n";

const CATEGORY_OPTIONS: Array<[Category | "ALL", Key]> = [
  ["ALL", "filter.all.categories"], ["BL_COMPARISON", "cat.BL_COMPARISON"], ["SI_REQUEST", "cat.SI_REQUEST"],
  ["INVOICE_QUERY", "cat.INVOICE_QUERY"], ["GENERAL", "cat.GENERAL"], ["SPAM", "cat.SPAM"],
];
const STATUS_OPTIONS: Array<[Status | "ALL", Key]> = [
  ["ALL", "filter.all.statuses"], ["MISMATCH", "status.MISMATCH"], ["NEEDS_REVIEW", "status.NEEDS_REVIEW"], ["OK", "status.OK"],
];
const SOURCE_OPTIONS: Array<[EmailSummary["source"] | "ALL", Key]> = [
  ["ALL", "filter.all.sources"], ["dataset", "source.dataset"], ["mailbox", "source.mailbox"], ["upload", "source.upload"],
];
type SortKey = "newest" | "oldest" | "severity" | "category" | "sender" | "subject";
const SORT_OPTIONS: Array<[SortKey, Key]> = [
  ["newest", "sort.newest"], ["oldest", "sort.oldest"], ["severity", "sort.severity"],
  ["category", "sort.category"], ["sender", "sort.sender"], ["subject", "sort.subject"],
];
const SEVERITY: Record<string, number> = { MISMATCH: 0, NEEDS_REVIEW: 1, OK: 2 };

export function InboxPage() {
  const [rows, setRows] = useState<EmailSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<Category | "ALL">("ALL");
  const [status, setStatus] = useState<Status | "ALL">("ALL");
  const [source, setSource] = useState<EmailSummary["source"] | "ALL">("ALL");
  const [sort, setSort] = useState<SortKey>("newest");
  const [announce, setAnnounce] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const { t } = useT();

  const load = () => api.emails().then(setRows).catch((e) => setError(String(e.message)));
  useEffect(() => { load(); }, []);

  const processed = useMemo(() => (rows ?? []).some((r) => r.result.status), [rows]);

  const filtered = useMemo(() => {
    const list = (rows ?? []).filter((r) =>
      (cat === "ALL" || r.result.category === cat) &&
      (status === "ALL" || (r.result.category === "BL_COMPARISON" && r.result.status === status)) &&
      (source === "ALL" || r.source === source) &&
      (!q || `${r.subject} ${r.from} ${r.email_id}`.toLowerCase().includes(q.toLowerCase())));
    const sev = (r: EmailSummary) => (r.result.category === "BL_COMPARISON" ? SEVERITY[r.result.status] ?? 3 : 4);
    const cmp: Record<SortKey, (a: EmailSummary, b: EmailSummary) => number> = {
      newest: (a, b) => b.email_id.localeCompare(a.email_id),
      oldest: (a, b) => a.email_id.localeCompare(b.email_id),
      severity: (a, b) => sev(a) - sev(b) || a.email_id.localeCompare(b.email_id),
      category: (a, b) => a.result.category.localeCompare(b.result.category) || a.email_id.localeCompare(b.email_id),
      sender: (a, b) => a.from.localeCompare(b.from),
      subject: (a, b) => a.subject.localeCompare(b.subject),
    };
    return [...list].sort(cmp[sort]);
  }, [rows, cat, status, source, q, sort]);

  const counts = useMemo(() => {
    const c = { total: rows?.length ?? 0, mismatch: 0, review: 0, ok: 0 };
    for (const r of rows ?? []) {
      if (r.result.category !== "BL_COMPARISON") continue;
      if (r.result.status === "MISMATCH") c.mismatch++;
      else if (r.result.status === "NEEDS_REVIEW") c.review++;
      else c.ok++;
    }
    return c;
  }, [rows]);

  const filtersActive = q !== "" || cat !== "ALL" || status !== "ALL" || source !== "ALL";

  function showStatus(s: Status | "ALL") {
    setStatus(s); setCat(s === "ALL" ? "ALL" : "BL_COMPARISON"); setSource("ALL"); setQ("");
    setSort(s === "ALL" ? "newest" : "severity");
    setAnnounce(s === "ALL" ? t("tile.showing") : `${t("tile.showing")}: ${t(STATUS_OPTIONS.find(([k]) => k === s)![1])}`);
    requestAnimationFrame(() => listRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }
  function clearFilters() { setQ(""); setCat("ALL"); setStatus("ALL"); setSource("ALL"); setSort("newest"); setAnnounce("Filters cleared."); }

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
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="hover-sheen inline-block">{t("inbox.title")}</h1>
          <p className="text-lg text-muted-foreground">{t("inbox.subtitle")}</p>
        </div>
        <Button size="lg" onClick={processInbox} disabled={busy}>
          <RefreshCw className={busy ? "size-5 animate-spin" : "size-5"} aria-hidden="true" />
          {busy ? t("inbox.processing") : t("inbox.process")}
        </Button>
      </div>
      <p className="sr-only" aria-live="polite">{announce}</p>

      <MailSources onChange={load} />

      <Stats items={[
        { label: t("tile.emails"), value: counts.total, tone: "blue", icon: Mail, onClick: () => showStatus("ALL"), active: !filtersActive },
        { label: t("tile.mismatch"), value: counts.mismatch, tone: "red", icon: XCircle, onClick: () => showStatus("MISMATCH"), active: status === "MISMATCH" },
        { label: t("tile.review"), value: counts.review, tone: "yellow", icon: AlertTriangle, onClick: () => showStatus("NEEDS_REVIEW"), active: status === "NEEDS_REVIEW" },
        { label: t("tile.clean"), value: counts.ok, tone: "green", icon: CheckCircle2, onClick: () => showStatus("OK"), active: status === "OK" },
      ]} />

      <div ref={listRef} className="scroll-mt-28 space-y-4">
        <form className="lift-soft grid gap-4 rounded-2xl border bg-card p-5 md:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr_1fr_auto]" onSubmit={(e) => e.preventDefault()} aria-label="Filter and sort the inbox">
          <div className="md:col-span-2 xl:col-span-1">
            <Label htmlFor="search">{t("filter.search")}</Label>
            <Input id="search" className="field h-11" placeholder={t("filter.search.ph")} value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="cat">{t("filter.category")}</Label>
            <select id="cat" className="w-full" value={cat} onChange={(e) => setCat(e.target.value as Category | "ALL")}>
              {CATEGORY_OPTIONS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
            </select>
          </div>
          <div>
            <Label htmlFor="status">{t("filter.status")}</Label>
            <select id="status" className="w-full" value={status} onChange={(e) => setStatus(e.target.value as Status | "ALL")}>
              {STATUS_OPTIONS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
            </select>
          </div>
          <div>
            <Label htmlFor="source">{t("filter.source")}</Label>
            <select id="source" className="w-full" value={source} onChange={(e) => setSource(e.target.value as EmailSummary["source"] | "ALL")}>
              {SOURCE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
            </select>
          </div>
          <div>
            <Label htmlFor="sort">{t("filter.sort")}</Label>
            <select id="sort" className="w-full" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
              {SORT_OPTIONS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <Button type="button" variant="outline" className="h-11 w-full" onClick={clearFilters} disabled={!filtersActive && sort === "newest"}>
              <Eraser className="size-4" aria-hidden="true" />{t("filter.clear")}
            </Button>
          </div>
        </form>

        <p className="text-sm text-muted-foreground" aria-live="polite">
          {t("inbox.showing", { n: filtered.length, total: rows?.length ?? 0 })}
          {status !== "ALL" && <> · <strong>{t(STATUS_OPTIONS.find(([k]) => k === status)![1])}</strong></>}
          {cat !== "ALL" && <> · <strong>{t(CATEGORY_OPTIONS.find(([k]) => k === cat)![1])}</strong></>}
          {source !== "ALL" && <> · <strong>{t(SOURCE_OPTIONS.find(([k]) => k === source)![1])}</strong></>}
        </p>

        {error && <p role="alert" className="rounded-2xl border border-bad bg-bad-bg p-4 text-bad">{t("inbox.apiError", { err: error })}</p>}
        {rows && !processed && !error && (
          <p className="rounded-2xl border bg-card p-4">{t("inbox.noResults")}</p>
        )}

        <div className="lift-soft overflow-x-auto rounded-2xl border bg-card">
          <Table>
            <caption className="sr-only">Inbox, {filtered.length} of {rows?.length ?? 0} emails shown</caption>
            <TableHeader>
              <TableRow>
                <TableHead scope="col">{t("col.email")}</TableHead>
                <TableHead scope="col" className="hidden md:table-cell">{t("col.from")}</TableHead>
                <TableHead scope="col" className="hidden md:table-cell">{t("col.category")}</TableHead>
                <TableHead scope="col" className="hidden md:table-cell">{t("col.status")}</TableHead>
                <TableHead scope="col" className="hidden md:table-cell">{t("col.fields")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.email_id} data-status={r.result.category === "BL_COMPARISON" ? r.result.status : "NONE"}>
                  <TableCell className="max-w-md">
                    <Link to={`/emails/${r.email_id}`} title={r.subject}
                      className="block truncate font-semibold underline-offset-2 hover:underline focus-visible:underline">
                      {r.subject || "(no subject)"}
                    </Link>
                    <div className="mt-1 flex flex-wrap items-center gap-2 md:hidden">
                      <CategoryChip category={r.result.category} />
                      {r.result.category === "BL_COMPARISON" && <StatusBadge status={r.result.status} />}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>{r.email_id}</span>
                      {r.source !== "dataset" && <span className="rounded-full bg-info-bg px-2 py-0.5 text-xs font-bold text-info">{r.source}</span>}
                      {r.attachments.length > 0 && <span className="inline-flex items-center gap-0.5"><Paperclip className="size-3.5" aria-hidden="true" />{r.attachments.length} <span className="sr-only">{t("col.attachments")}</span></span>}
                    </div>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">{r.from}</TableCell>
                  <TableCell className="hidden md:table-cell"><CategoryChip category={r.result.category} /></TableCell>
                  <TableCell className="hidden md:table-cell">{r.result.category === "BL_COMPARISON" ? <StatusBadge status={r.result.status} /> : <span className="text-sm text-muted-foreground">-</span>}</TableCell>
                  <TableCell className="hidden text-sm md:table-cell">{r.result.defect_fields.join(", ")}</TableCell>
                </TableRow>
              ))}
              {rows && filtered.length === 0 && (
                <TableRow><TableCell colSpan={5} className="py-12 text-center text-muted-foreground">{t("inbox.none")} <button type="button" className="underline" onClick={clearFilters}>{t("inbox.clearFilters")}</button></TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
