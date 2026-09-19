import { HashRouter, Route, Routes } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Layout } from "@/components/Layout";
import { InboxPage } from "@/pages/InboxPage";
import { ComparePage } from "@/pages/ComparePage";
import { ImpactPage } from "@/pages/ImpactPage";
import { InvoicesPage } from "@/pages/InvoicesPage";
import { HelpPage } from "@/pages/HelpPage";
import { AccessibilityPage, CookiesPage, PrivacyPage, TermsPage } from "@/pages/LegalPages";

// HashRouter so the same build works on static hosting and inside the Android WebView.
export default function App() {
  return (
    <TooltipProvider delayDuration={150}>
      <HashRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<InboxPage />} />
            <Route path="emails/:id" element={<ComparePage />} />
            <Route path="impact" element={<ImpactPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="help" element={<HelpPage />} />
            <Route path="privacy" element={<PrivacyPage />} />
            <Route path="terms" element={<TermsPage />} />
            <Route path="cookies" element={<CookiesPage />} />
            <Route path="accessibility" element={<AccessibilityPage />} />
            <Route path="*" element={<p>Page not found.</p>} />
          </Route>
        </Routes>
      </HashRouter>
    </TooltipProvider>
  );
}
