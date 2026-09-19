import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type InvoiceRecord } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Stats } from "@/components/Stats";

export function InvoicesPage() {
  const [rows, setRows] = useState<InvoiceRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => { api.invoices().then(setRows).catch((e) => setError(e.message)); }, []);

  const filtered = useMemo(() => (rows ?? []).filter((r) => !q ||
    [r.subject, r.sender, ...r.invoice_numbers, ...r.order_refs, ...r.amounts].join(" ").toLowerCase().includes(q.toLowerCase())), [rows, q]);

  const topics = useMemo(() => {
    const m = new Map<string, number>();
    for (const r of rows ?? []) m.set(r.topic, (m.get(r.topic) ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Invoices and receipts</h1>
        <p className="text-sm text-muted-foreground">Billing emails with the invoice numbers, order references and amounts found in them. Values are read from the email text; hover a number to see the line it came from.</p>
      </div>

      <Stats items={[
        { label: "Billing emails", value: rows?.length ?? 0 },
        ...topics.slice(0, 3).map(([t, n]) => ({ label: t, value: n })),
      ]} />

      <div className="max-w-md">
        <Label htmlFor="inv-q">Search</Label>
        <Input id="inv-q" placeholder="Invoice no., order ref, amount, sender" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>

      {error && <p role="alert" className="text-sm text-bad">Could not load invoices: {error}. Process the inbox first.</p>}
      {rows && rows.length === 0 && <p className="text-sm text-muted-foreground">No billing emails yet. Choose <strong>Process inbox</strong> on the Inbox page.</p>}

      <div className="overflow-x-auto rounded-md border">
        <Table>
          <caption className="sr-only">Billing emails, {filtered.length} shown</caption>
          <TableHeader><TableRow>
            <TableHead scope="col">Email</TableHead><TableHead scope="col">Topic</TableHead>
            <TableHead scope="col">Invoice no.</TableHead><TableHead scope="col">Order ref</TableHead><TableHead scope="col">Amount</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {filtered.map((r) => (
              <TableRow key={r.email_id}>
                <TableCell className="max-w-md">
                  <Link to={`/emails/${r.email_id}`} title={r.subject} className="block truncate font-medium hover:underline focus-visible:underline">{r.subject}</Link>
                  <div className="text-xs text-muted-foreground">{r.email_id} · {r.sender}</div>
                </TableCell>
                <TableCell className="text-sm capitalize">{r.topic}</TableCell>
                <TableCell><Nums items={r.invoice_numbers} evidence={r.evidence} /></TableCell>
                <TableCell className="font-mono text-xs">{r.order_refs.join(", ") || "—"}</TableCell>
                <TableCell><Nums items={r.amounts} evidence={r.evidence} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function Nums({ items, evidence }: { items: string[]; evidence: string[] }) {
  if (items.length === 0) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <span className="font-mono text-xs">
      {items.map((it, i) => {
        const src = evidence.find((e) => e.includes(it.replace(/^[A-Z$]+\s/, "")));
        const node = <span key={it}>{i > 0 && ", "}{it}</span>;
        return src ? (
          <Tooltip key={it}><TooltipTrigger asChild><button type="button" className="underline decoration-dotted">{node}</button></TooltipTrigger>
            <TooltipContent className="max-w-sm text-xs">{src}</TooltipContent></Tooltip>
        ) : node;
      })}
    </span>
  );
}
