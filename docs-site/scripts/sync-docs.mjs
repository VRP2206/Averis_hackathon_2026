// Pulls the public-safe documents out of ../docs into content/ so there is one source of truth.
//
// This is an ALLOW-list on purpose: only the files named below are ever published. Internal notes in
// ../docs (PLAN, TODO, HANDOFF, COMPLIANCE, AWS-DEPLOYMENT, ...) are never picked up, even by accident.
// The generated files are git-ignored (see .gitignore): edit the source in ../docs, not the copy.
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const site = resolve(here, "..");
const repo = resolve(site, "..");
const content = join(site, "content");

/** source (relative to the repo) -> page (relative to content/) */
const PAGES = {
  "docs/USER-GUIDE.md": "guide/user-guide.md",
  "docs/test-emails/README.md": "guide/test-emails.md",
  "docs/DEMO-ANDROID.md": "guide/android.md",
  "docs/ARCHITECTURE.md": "concepts/how-it-works.md",
};

const banner = (src) =>
  `<!-- Generated from ${src} by docs-site/scripts/sync-docs.mjs. Edit the source file, not this copy. -->\n\n`;

function write(target, text) {
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, text, "utf8");
}

for (const [src, dest] of Object.entries(PAGES)) {
  const from = join(repo, src);
  if (!existsSync(from)) {
    console.warn(`sync-docs: ${src} not found, skipping`);
    continue;
  }
  let text = readFileSync(from, "utf8");
  if (src.endsWith("test-emails/README.md")) {
    // make each file name in the table a download link
    text = text.replace(/^\| (\d\d-[a-z0-9-]+) \|/gm, (_m, name) => `| [${name}](/test-emails/${name}.eml) |`);
  }
  if (src.endsWith("ARCHITECTURE.md")) {
    // a wide left-to-right diagram shrinks to unreadable on the page: draw it top-down
    text = text.replace(/flowchart LR/g, "flowchart TD");
  }
  write(join(content, dest), banner(src) + text);
}

// static assets: screenshots, sample emails, logo
const copies = [
  ["docs/screenshots", "public/screenshots", (f) => f.endsWith(".png")],
  ["docs/test-emails", "public/test-emails", (f) => f.endsWith(".eml")],
];
for (const [from, to, keep] of copies) {
  const dir = join(repo, from);
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir).filter(keep)) {
    mkdirSync(join(content, to), { recursive: true });
    cpSync(join(dir, f), join(content, to, f));
  }
}
for (const f of ["logo.svg", "favicon.svg"]) {
  const from = join(repo, "web/public", f);
  if (existsSync(from)) {
    mkdirSync(join(content, "public"), { recursive: true });
    cpSync(from, join(content, "public", f));
  }
}
console.log("sync-docs: done");
