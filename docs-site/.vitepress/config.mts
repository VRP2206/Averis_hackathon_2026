import { defineConfig } from "vitepress";
import { withMermaid } from "vitepress-plugin-mermaid";

const APP_URL = "https://shipdoc.org";
const REPO_URL = "https://github.com/VRP2206/Averis_hackathon_2026";

export default withMermaid(
  defineConfig({
    title: "shipdoc docs",
    description: "Documentation for shipdoc: check every draft Bill of Lading against its Shipping Instruction, and hand what it cannot decide to a person.",
    lang: "en",
    srcDir: "content",
    lastUpdated: true,
    cleanUrls: false, // plain .html files work on any static host, no rewrite rules needed
    head: [
      ["link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
      ["meta", { name: "theme-color", content: "#5B4BD6" }],
    ],
    // localhost links, and the downloadable sample emails (they live in public/, so VitePress cannot see them as pages)
    ignoreDeadLinks: [/^https?:\/\/localhost/, /^http:\/\/127\.0\.0\.1/, /^\/test-emails\/.+\.eml$/],
    themeConfig: {
      logo: "/logo.svg",
      siteTitle: "shipdoc docs",
      nav: [
        { text: "Guide", link: "/guide/getting-started", activeMatch: "/guide/" },
        { text: "Concepts", link: "/concepts/how-it-works", activeMatch: "/concepts/" },
        { text: "Reference", link: "/reference/api", activeMatch: "/reference/" },
        { text: "Deploy", link: "/deploy/run-locally", activeMatch: "/deploy/" },
        { text: "Open the app", link: APP_URL },
      ],
      sidebar: [
        {
          text: "Guide",
          items: [
            { text: "Getting started", link: "/guide/getting-started" },
            { text: "User guide", link: "/guide/user-guide" },
            { text: "Test emails", link: "/guide/test-emails" },
            { text: "Android app", link: "/guide/android" },
            { text: "Troubleshooting", link: "/guide/troubleshooting" },
          ],
        },
        {
          text: "Concepts",
          items: [
            { text: "How shipdoc decides", link: "/concepts/how-it-works" },
            { text: "Categories, statuses and reasons", link: "/concepts/statuses" },
            { text: "Privacy and data handling", link: "/concepts/privacy" },
          ],
        },
        {
          text: "Reference",
          items: [
            { text: "API", link: "/reference/api" },
            { text: "Configuration", link: "/reference/configuration" },
            { text: "Command line", link: "/reference/cli" },
          ],
        },
        {
          text: "Deploy",
          items: [
            { text: "Run it locally", link: "/deploy/run-locally" },
            { text: "Deploy on AWS", link: "/deploy/aws" },
          ],
        },
      ],
      socialLinks: [{ icon: "github", link: REPO_URL }],
      search: { provider: "local" },
      outline: { level: [2, 3] },
      editLink: {
        // This function is shipped to the browser, so it must not use anything defined outside it.
        // Pages copied from ../docs by scripts/sync-docs.mjs open their real source file.
        pattern: ({ filePath }) => {
          const synced: Record<string, string> = {
            "guide/user-guide.md": "docs/USER-GUIDE.md",
            "guide/test-emails.md": "docs/test-emails/README.md",
            "guide/android.md": "docs/DEMO-ANDROID.md",
            "concepts/how-it-works.md": "docs/ARCHITECTURE.md",
          };
          return `https://github.com/VRP2206/Averis_hackathon_2026/edit/main/${synced[filePath] ?? "docs-site/content/" + filePath}`;
        },
        text: "Edit this page on GitHub",
      },
      footer: {
        message: "A student prototype built for the Averis × Monash Hackathon 2026. Not an Averis product.",
        copyright: "Team Claude's Plan",
      },
    },
    mermaid: {},
    mermaidPlugin: { class: "mermaid" },
  }),
);
