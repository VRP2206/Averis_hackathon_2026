import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Plug, RefreshCw, Unplug, Upload } from "lucide-react";
import { api, type MailboxStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const PRESETS: Record<string, string> = { Gmail: "imap.gmail.com", "Outlook / Microsoft 365": "outlook.office365.com", Yahoo: "imap.mail.yahoo.com" };

/** "Where do emails come from?" controls: connect a real mailbox over IMAP, or drop in a .eml file. */
export function MailSources({ onChange }: { onChange: () => void }) {
  const [status, setStatus] = useState<MailboxStatus>({ connected: false });
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => api.mailbox().then(setStatus).catch(() => undefined);
  useEffect(() => { load(); }, []);

  async function refresh() {
    setBusy("refresh");
    try { const r = await api.mailboxRefresh(); setMsg(`Fetched ${r.fetched} new email(s).`); onChange(); }
    catch (e) { setMsg((e as Error).message); } finally { setBusy(null); }
  }
  async function disconnect() {
    setBusy("disconnect");
    try { await api.mailboxDisconnect(); setStatus({ connected: false }); setMsg("Mailbox disconnected."); onChange(); }
    finally { setBusy(null); }
  }
  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return;
    setBusy("upload");
    try { const r = await api.upload(f); setMsg(`Processed ${f.name}: ${r.category}${r.status ? ` / ${r.status}` : ""}.`); onChange(); }
    catch (err) { setMsg((err as Error).message); } finally { setBusy(null); if (fileRef.current) fileRef.current.value = ""; }
  }

  return (
    <section aria-labelledby="sources" className="lift rounded-2xl border-l-8 border-l-g-blue bg-card p-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="sources" className="flex items-center gap-2 text-base font-semibold"><Mail className="size-5 text-primary" aria-hidden="true" />Email sources</h2>
        <p className="text-sm text-muted-foreground">
          {status.connected ? <>Connected to <strong>{status.user}</strong> ({status.host}, {status.folder}).</> : "Hackathon dataset loaded. Connect a real mailbox or upload an email."}
        </p>
        <div className="ml-auto flex flex-wrap gap-2">
          {status.connected ? (
            <>
              <Button variant="outline" size="sm" onClick={refresh} disabled={busy !== null}><RefreshCw className={busy === "refresh" ? "size-4 animate-spin" : "size-4"} aria-hidden="true" />Fetch new mail</Button>
              <Button variant="ghost" size="sm" onClick={disconnect} disabled={busy !== null}><Unplug className="size-4" aria-hidden="true" />Disconnect</Button>
            </>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setOpen(true)}><Plug className="size-4" aria-hidden="true" />Connect mailbox</Button>
          )}
          <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()} disabled={busy === "upload"}>
            <Upload className="size-4" aria-hidden="true" />{busy === "upload" ? "Processing…" : "Upload .eml"}
          </Button>
          <input ref={fileRef} type="file" accept=".eml,message/rfc822" className="sr-only" onChange={onFile} aria-label="Upload an .eml email file" />
        </div>
      </div>
      <p className="mt-2 text-sm" aria-live="polite">{msg}</p>
      <ConnectDialog open={open} onOpenChange={setOpen} onConnected={(s) => { setStatus(s); setMsg(`Connected. Fetched ${s.messages_in_folder ?? 0} messages in folder; processed the latest ${s.cached ?? ""}.`); onChange(); }} />
    </section>
  );
}

function ConnectDialog({ open, onOpenChange, onConnected }: { open: boolean; onOpenChange: (o: boolean) => void; onConnected: (s: MailboxStatus) => void }) {
  const [host, setHost] = useState(PRESETS.Gmail);
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [folder, setFolder] = useState("INBOX");
  const [limit, setLimit] = useState(50);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      const r = await api.mailboxConnect({ host, user, password, folder, limit });
      onConnected({ connected: true, host, user, folder, cached: r.processed, messages_in_folder: r.messages_in_folder });
      setPassword(""); onOpenChange(false);
    } catch (ex) { setErr((ex as Error).message); } finally { setBusy(false); }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Connect a mailbox</DialogTitle>
            <DialogDescription>Read-only IMAP access. For Gmail, turn on 2-step verification and create an <strong>App Password</strong>; your normal password will not work. Credentials stay in the server's memory for this session and are never stored.</DialogDescription>
          </DialogHeader>
          <div>
            <Label htmlFor="provider">Provider</Label>
            <select id="provider" className="flex h-10 w-full rounded-md border bg-transparent px-3" value={host} onChange={(e) => setHost(e.target.value)}>
              {Object.entries(PRESETS).map(([n, h]) => <option key={h} value={h}>{n}</option>)}
            </select>
          </div>
          <div><Label htmlFor="imap-host">IMAP host</Label><Input id="imap-host" value={host} onChange={(e) => setHost(e.target.value)} required /></div>
          <div><Label htmlFor="imap-user">Email address</Label><Input id="imap-user" type="email" autoComplete="username" value={user} onChange={(e) => setUser(e.target.value)} required /></div>
          <div><Label htmlFor="imap-pass">App password</Label><Input id="imap-pass" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label htmlFor="imap-folder">Folder</Label><Input id="imap-folder" value={folder} onChange={(e) => setFolder(e.target.value)} /></div>
            <div><Label htmlFor="imap-limit">Latest N messages</Label><Input id="imap-limit" type="number" min={1} max={500} value={limit} onChange={(e) => setLimit(Number(e.target.value))} /></div>
          </div>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" className="mt-1 size-4 shrink-0" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
            <span>I am authorised to connect this mailbox, and I understand its emails and attachments will be processed as described in the <Link className="underline" to="/privacy">privacy policy</Link>.</span>
          </label>
          {err && <p role="alert" className="text-sm text-bad">{err}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={busy || !consent}>{busy ? "Connecting…" : "Connect and fetch"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
