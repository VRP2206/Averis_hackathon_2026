import { useState } from "react";
import { Link } from "react-router-dom";
import { Download, Sparkles } from "lucide-react";
import { api, type EmailResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";

const SAMPLES = [
  { file: "sample-mismatch.eml", label: "Mismatch: wrong port and container count" },
  { file: "sample-ok.eml", label: "Clean pair: everything matches" },
  { file: "sample-wrong-doc.eml", label: "Wrong document: an invoice sent as the BL" },
];

export function HelpPage() {
  const [busy, setBusy] = useState<string | null>(null);
  const [result, setResult] = useState<EmailResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function trySample(file: string) {
    setBusy(file); setErr(null);
    try {
      const blob = await (await fetch(`/samples/${file}`)).blob();
      setResult(await api.upload(new File([blob], file, { type: "message/rfc822" })));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  }

  return (
    <div className="space-y-10">
      <section className="grid items-center gap-8 lg:grid-cols-2">
        <div>
          <h1 className="hover-sheen inline-block">How to get your inbox in</h1>
          <p className="mt-3 text-xl text-muted-foreground">Three ways in, one pipeline out. Start with a sample, then connect a real mailbox.</p>
        </div>
        <img src="/hero.svg" alt="Emails flow from a mailbox through SDOC and come out as checked Bills of Lading" className="lift w-full rounded-3xl" />
      </section>

      <section aria-labelledby="try">
        <h2 id="try" className="hover-sheen inline-block">1. Try it in ten seconds</h2>
        <p className="mb-4 text-muted-foreground">Each sample is a real <code>.eml</code> file with an SI and a draft BL attached. One click runs it through the pipeline.</p>
        <div className="grid gap-4 md:grid-cols-3">
          {SAMPLES.map((s, i) => (
            <Card key={s.file} className={["border-t-8 border-t-g-red", "border-t-8 border-t-g-green", "border-t-8 border-t-g-yellow"][i]}>
              <CardHeader><CardTitle className="text-lg">{s.label}</CardTitle></CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Button onClick={() => trySample(s.file)} disabled={busy !== null}><Sparkles className="size-4" aria-hidden="true" />{busy === s.file ? "Running…" : "Run this sample"}</Button>
                <Button asChild variant="outline"><a href={`/samples/${s.file}`} download><Download className="size-4" aria-hidden="true" />Download .eml</a></Button>
              </CardContent>
            </Card>
          ))}
        </div>
        {err && <p role="alert" className="mt-3 text-bad">{err}. Is the API running? Check the address under the gear icon.</p>}
        {result && (
          <div role="status" className="lift mt-4 flex flex-wrap items-center gap-3 rounded-2xl border-l-8 border-l-g-blue bg-card p-5">
            <span className="text-lg font-bold">Result:</span>
            <StatusBadge status={result.status} />
            {result.defect_fields.length > 0 && <span>fields: {result.defect_fields.join(", ")}</span>}
            {result.review_reason && <span>reason: {result.review_reason.replace("_", " ")}</span>}
            <Button asChild variant="outline" size="sm"><Link to={`/emails/${result.email_id}`}>Open the comparison</Link></Button>
          </div>
        )}
      </section>

      <section aria-labelledby="gmail" className="grid gap-6 lg:grid-cols-2">
        <Card className="border-t-8 border-t-g-red">
          <CardHeader><CardTitle className="text-2xl">2. Connect Gmail</CardTitle></CardHeader>
          <CardContent>
            <ol className="list-decimal space-y-3 pl-6">
              <li>In your Google Account open <strong>Security → 2-Step Verification</strong> and turn it on (required for app passwords).</li>
              <li>Still under Security, open <strong>App passwords</strong> (search "App passwords" in the account search bar). Name it <em>SDOC</em> and choose <strong>Create</strong>. Google shows a 16-character password once; copy it.</li>
              <li>Back here, open <Link className="underline" to="/">Inbox</Link> and choose <strong>Connect mailbox</strong>. Provider <em>Gmail</em>, your address, and paste the app password.</li>
              <li>Leave folder <code>INBOX</code> and latest <code>50</code>, tick the authorisation box, then <strong>Connect and fetch</strong>. The newest 50 emails are triaged in a few seconds and tagged <em>mailbox</em>.</li>
              <li>New mail later? Choose <strong>Fetch new mail</strong>. Done for the day? <strong>Disconnect</strong> forgets the credentials.</li>
            </ol>
            <p className="mt-3 text-sm text-muted-foreground">Tip for the demo: send yourself an email with <code>sample-mismatch.eml</code>'s two attachments and the subject <code>TO CONFIRM DOCS _ demo</code>, then Fetch new mail.</p>
          </CardContent>
        </Card>
        <Card className="border-t-8 border-t-g-blue">
          <CardHeader><CardTitle className="text-2xl">3. Outlook, 365, or any IMAP</CardTitle></CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-6">
              <li><strong>Outlook / Microsoft 365:</strong> host <code>outlook.office365.com</code>. Personal accounts use your password with 2FA app password; work tenants may need IMAP enabled by the admin.</li>
              <li><strong>Yahoo:</strong> host <code>imap.mail.yahoo.com</code>, app password from Account Security.</li>
              <li><strong>Anything else:</strong> choose Gmail in the provider list, then overwrite the IMAP host field.</li>
            </ul>
            <h3 className="mt-5 text-lg font-semibold">Or upload a single email</h3>
            <p>In Gmail open the message → <strong>⋮ → Download message</strong>; in Outlook drag it to the desktop. Then <strong>Upload .eml</strong> on the Inbox page. Attachments travel inside the file.</p>
            <h3 className="mt-5 text-lg font-semibold">What is read, what is kept</h3>
            <p className="text-sm text-muted-foreground">Read-only IMAP. Credentials live in server memory for this session only. Attachments are cached so the compare view can show evidence. See the <Link className="underline" to="/privacy">privacy policy</Link>.</p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
