import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { business as b } from "@/content/business";

function Page({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="prose-sm mx-auto max-w-3xl space-y-4 [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-semibold [&_ul]:list-disc [&_ul]:pl-6">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-muted-foreground">Last updated {b.lastUpdated}. {b.productName} is a student prototype built by team {b.teamName} for the {b.event}. It is not an Averis product.</p>
      {children}
      <p className="text-sm">Questions: <a className="underline" href={`mailto:${b.contactEmail}`}>{b.contactEmail}</a></p>
    </article>
  );
}

export function PrivacyPage() {
  return (
    <Page title="Privacy Policy">
      <h2>Who we are</h2>
      <p>{b.productName} is operated by team {b.teamName} ({b.members.join(", ")}), students participating in the {b.event} in {b.country}. We are the data controller for the small amount of personal data described below.</p>
      <h2>What we collect and why</h2>
      <ul>
        <li><strong>Reviewer name</strong> (optional) when you override or approve a result, so the team can see who made a decision. Legal basis: your consent, given on the form. If you leave the default value, no name is stored.</li>
        <li><strong>Email records and attachments in the demo inbox.</strong> These are a synthetic dataset supplied by the hackathon organisers. Company and person names in it are fictional or used for realism only.</li>
        <li><strong>Theme and filter preferences</strong>, kept in your browser's local storage and never sent to us.</li>
      </ul>
      <p>We do not use analytics, advertising, tracking pixels or third-party embeds. We do not sell or share personal data.</p>
      <h2>AI processing</h2>
      <p>When an AI model is enabled, the text of emails and attachments may be sent to Anthropic (Claude API) or Amazon Web Services (Amazon Bedrock) to classify emails and read document fields. These providers process the data to return a result and, under their business terms, do not use it to train models. The comparison decision itself is made by our own code.</p>
      <h2>Where data is stored</h2>
      <p>Results and reviewer decisions are stored on the server that hosts the API (during the hackathon, an AWS account operated by the team). If this is outside {b.country}, that is a cross-border transfer under the Personal Data Protection Act 2010; we only do this for the synthetic demo data and reviewer names of team members.</p>
      <h2>Retention</h2>
      <p>Demo data and results are deleted when the hackathon ends or on request, whichever is earlier.</p>
      <h2>Your rights</h2>
      <p>Under the PDPA 2010 (and the GDPR if you are in the EU) you can ask us to access, correct or delete personal data about you, or withdraw consent. Email {b.contactEmail}; we respond within 21 days.</p>
      <h2>Changes</h2>
      <p>We will update this page if the product starts processing real mailbox data; that would require a new notice to affected staff and a data processing agreement with the organisation concerned.</p>
    </Page>
  );
}

export function TermsPage() {
  return (
    <Page title="Terms of Use">
      <h2>What this is</h2>
      <p>{b.productName} is a prototype demonstrating automated triage of shipping emails and comparison of Shipping Instructions with draft Bills of Lading. It is provided for evaluation during the {b.event} only.</p>
      <h2>No professional advice, no guarantee</h2>
      <p>The tool <em>recommends</em>. Every result must be checked by a qualified person before any document is released, amended or relied upon. Accuracy figures shown in the app were measured on a synthetic dataset and do not predict performance on real documents. To the fullest extent permitted by law, the team excludes liability for losses arising from use of the prototype.</p>
      <h2>No purchases, no refunds</h2>
      <p>Nothing is sold through this site or app, and no payment details are collected. A refund policy therefore does not apply.</p>
      <h2>Acceptable use</h2>
      <p>Do not upload data you are not authorised to share, attempt to access other users' data, or interfere with the service. Do not use the tool to make automated decisions about individuals.</p>
      <h2>Intellectual property</h2>
      <p>The source code is available at <a className="underline" href={b.repoUrl}>{b.repoUrl}</a> under its stated licence. Third-party components are credited in the repository. The dataset belongs to the hackathon organisers and may not be redistributed.</p>
      <h2>Governing law</h2>
      <p>These terms are governed by the laws of {b.country}.</p>
      <p>See also our <Link className="underline" to="/privacy">Privacy Policy</Link>, <Link className="underline" to="/cookies">Cookie Policy</Link> and <Link className="underline" to="/accessibility">Accessibility statement</Link>.</p>
    </Page>
  );
}

export function CookiesPage() {
  return (
    <Page title="Cookie Policy">
      <h2>We do not set cookies</h2>
      <p>This site and app set no cookies and load no third-party scripts, fonts, analytics or embeds. Because there are no non-essential cookies or trackers, no consent banner is required under the PDPA 2010 or, for EU visitors, the ePrivacy rules and GDPR.</p>
      <h2>Local storage</h2>
      <p>We keep two preferences in your browser's local storage: your theme choice and, if you entered one, your reviewer name. This information never leaves your device except when you save an override, which sends the reviewer name with your decision. You can clear it at any time from your browser settings.</p>
      <h2>If this changes</h2>
      <p>If analytics or other cookies are ever added, this page will list them and a consent control will be added before they are set.</p>
    </Page>
  );
}

export function AccessibilityPage() {
  return (
    <Page title="Accessibility">
      <p>We aim to meet WCAG 2.1 level AA. What is in place:</p>
      <ul>
        <li>All functions work with a keyboard: visible focus, a skip link, Escape closes dialogs, Enter submits forms.</li>
        <li>Status is shown with text and an icon, never colour alone; colour contrast is at least 4.5:1 in light and dark themes.</li>
        <li>Tables have captions and header cells; forms have labelled controls; live regions announce results of actions.</li>
        <li>Decorative icons are hidden from assistive technology; meaningful ones have text alternatives.</li>
        <li>Animation is disabled when your system asks for reduced motion.</li>
      </ul>
      <p>Known limits: the prototype has been tested by keyboard and inspection, not yet with screen-reader users. If something does not work for you, email {b.contactEmail} and we will fix it or provide the information another way.</p>
    </Page>
  );
}
