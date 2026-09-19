import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Inbox, Moon, Receipt, Ship, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { business } from "@/content/business";
import { cn } from "@/lib/utils";

function useTheme() {
  const [dark, setDark] = useState(() => {
    try {
      const saved = localStorage.getItem("sdoc.theme");
      if (saved) return saved === "dark";
    } catch { /* storage unavailable */ }
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("sdoc.theme", dark ? "dark" : "light"); } catch { /* ignore */ }
  }, [dark]);
  return { dark, toggle: () => setDark((d) => !d) };
}

const nav = [
  { to: "/", label: "Inbox", icon: Inbox, end: true },
  { to: "/invoices", label: "Invoices", icon: Receipt },
  { to: "/impact", label: "Impact", icon: BarChart3 },
];

export function Layout() {
  const { dark, toggle } = useTheme();
  return (
    <div className="flex min-h-svh flex-col">
      <a href="#main" className="skip-link">Skip to main content</a>
      <header className="header-band sticky top-0 z-40 border-b backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2">
            <Ship className="size-6 text-primary" aria-hidden="true" />
            <span className="sheen font-display text-2xl font-semibold">{business.productName}</span>
          </NavLink>
          <nav aria-label="Primary" className="flex items-center gap-1">
            {nav.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end}
                className={({ isActive }) => cn("flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[0.95rem] font-semibold",
                  isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/60")}>
                <Icon className="size-4" aria-hidden="true" />{label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto">
            <Button variant="ghost" size="icon" onClick={toggle} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}>
              {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
          </div>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 text-xs text-muted-foreground">
          <p>
            Student prototype by team {business.teamName} for the {business.event}. Not an Averis product.
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
    </div>
  );
}
