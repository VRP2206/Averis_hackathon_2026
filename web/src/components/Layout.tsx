import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, CircleHelp, Inbox, Moon, Receipt, Settings, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { business } from "@/content/business";
import { API_URL, DEFAULT_API_URL, setApiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

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

const nav = [
  { to: "/", label: "Inbox", icon: Inbox, end: true, color: "text-g-blue" },
  { to: "/invoices", label: "Invoices", icon: Receipt, color: "text-g-red" },
  { to: "/impact", label: "Impact", icon: BarChart3, color: "text-g-green" },
  { to: "/help", label: "Help", icon: CircleHelp, color: "text-g-yellow" },
];

export function Layout() {
  const { dark, toggle } = useTheme();
  const [settingsOpen, setSettingsOpen] = useState(false);
  return (
    <div className="flex min-h-svh flex-col">
      <div className="blobs" aria-hidden="true"><span className="b1" /><span className="b2" /><span className="b3" /><span className="b4" /></div>
      <a href="#main" className="skip-link">Skip to main content</a>
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
                <Icon className={cn("size-5", color)} aria-hidden="true" />{label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={() => setSettingsOpen(true)} aria-label="Settings: API server address">
              <Settings className="size-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={toggle} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}>
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
            Student prototype by team <strong>{business.teamName}</strong> for the {business.event}. Not an Averis product.
            Contact: <a className="underline" href={`mailto:${business.contactEmail}`}>{business.contactEmail}</a>
          </p>
          <nav aria-label="Legal" className="flex gap-4">
            <NavLink className="underline" to="/privacy">Privacy</NavLink>
            <NavLink className="underline" to="/terms">Terms</NavLink>
            <NavLink className="underline" to="/cookies">Cookies</NavLink>
            <NavLink className="underline" to="/accessibility">Accessibility</NavLink>
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
