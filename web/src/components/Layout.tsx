import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, CircleHelp, Globe, Inbox, Moon, Receipt, Settings, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { business } from "@/content/business";
import { API_URL, DEFAULT_API_URL, setApiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { LANGS, useT, type Key, type Lang } from "@/lib/i18n";

function useTheme() {
  // Light (Gmail white) by default; a saved choice wins.
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem("sdoc.theme") === "dark"; } catch { return false; }
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("sdoc.theme", dark ? "dark" : "light"); } catch { /* ignore */ }
  }, [dark]);
  return { dark, toggle: () => setDark((d) => !d) };
}

const nav: Array<{ to: string; label: Key; icon: typeof Inbox; end?: boolean; color: string }> = [
  { to: "/", label: "nav.inbox", icon: Inbox, end: true, color: "text-g-blue" },
  { to: "/invoices", label: "nav.invoices", icon: Receipt, color: "text-g-red" },
  { to: "/impact", label: "nav.impact", icon: BarChart3, color: "text-g-green" },
  { to: "/help", label: "nav.help", icon: CircleHelp, color: "text-g-yellow" },
];

export function Layout() {
  const { dark, toggle } = useTheme();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { t, lang, setLang } = useT();
  return (
    <div className="flex min-h-svh flex-col">
      <div className="blobs" aria-hidden="true"><span className="b1" /><span className="b2" /><span className="b3" /><span className="b4" /></div>
      <a href="#main" className="skip-link">{t("nav.skip")}</a>
      <header className="sticky top-0 z-40 bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex h-20 max-w-7xl items-center gap-5 px-5">
          <NavLink to="/" className="flex items-center gap-3">
            <img src="/logo.svg" alt="" width="44" height="44" className="drop-shadow-md transition-transform duration-500 hover:rotate-[-8deg] hover:scale-110" />
            <span className="sheen font-display text-4xl font-semibold">{business.productName}</span>
          </NavLink>
          <nav aria-label="Primary" className="flex items-center gap-1 overflow-x-auto">
            {nav.map(({ to, label, icon: Icon, end, color }) => (
              <NavLink key={to} to={to} end={end}
                className={({ isActive }) => cn("flex items-center gap-2 rounded-full px-4 py-2 text-base font-bold transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg",
                  isActive ? "bg-accent text-accent-foreground shadow-md" : "text-muted-foreground hover:bg-accent/70")}>
                <Icon className={cn("size-5", color)} aria-hidden="true" />{t(label)}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <label className="flex items-center gap-2 rounded-full border-2 border-g-blue/50 bg-card px-3 py-1.5 shadow-md transition hover:-translate-y-0.5 hover:shadow-lg">
              <Globe className="size-5 text-g-blue" aria-hidden="true" />
              <span className="sr-only">{t("nav.language")}</span>
              <select aria-label={t("nav.language")} className="!h-auto !border-0 !bg-transparent !p-0 !shadow-none font-bold" value={lang} onChange={(e) => setLang(e.target.value as Lang)}>
                {LANGS.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
              </select>
            </label>
            <Button variant="ghost" size="icon" onClick={() => setSettingsOpen(true)} aria-label={t("nav.settings")}>
              <Settings className="size-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={toggle} aria-label={dark ? t("nav.theme.light") : t("nav.theme.dark")}>
              {dark ? <Sun className="size-5" /> : <Moon className="size-5" />}
            </Button>
          </div>
        </div>
        <div className="g-stripe" aria-hidden="true" />
      </header>
      <main id="main" tabIndex={-1} className="mx-auto w-full max-w-7xl flex-1 px-5 py-8">
        <Outlet />
      </main>
      <footer className="border-t bg-background/80">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-5 text-sm text-muted-foreground">
          <p>
            {t("footer.line", { team: business.teamName, event: business.event })}{" "}
            {t("footer.contact")}: <a className="underline" href={`mailto:${business.contactEmail}`}>{business.contactEmail}</a>
          </p>
          <nav aria-label="Legal" className="flex gap-4">
            <NavLink className="underline" to="/privacy">{t("footer.privacy")}</NavLink>
            <NavLink className="underline" to="/terms">{t("footer.terms")}</NavLink>
            <NavLink className="underline" to="/cookies">{t("footer.cookies")}</NavLink>
            <NavLink className="underline" to="/accessibility">{t("footer.accessibility")}</NavLink>
          </nav>
        </div>
      </footer>
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

function SettingsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const [url, setUrl] = useState(API_URL);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setApiUrl(url); location.reload(); }}>
          <DialogHeader>
            <DialogTitle>API server</DialogTitle>
            <DialogDescription>Where this dashboard reads from. On the Android emulator use <code>http://10.0.2.2:8000</code>; on a phone use your laptop's IP, e.g. <code>http://192.168.1.20:8000</code> (start the API with <code>sdoc serve --host 0.0.0.0</code>).</DialogDescription>
          </DialogHeader>
          <div>
            <Label htmlFor="api-url">API base URL</Label>
            <Input id="api-url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder={DEFAULT_API_URL} />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => { setApiUrl(""); location.reload(); }}>Reset to default</Button>
            <Button type="submit">Save and reload</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
