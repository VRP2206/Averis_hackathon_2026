# shipdoc documentation site (docs.shipdoc.org)

A static site built with [VitePress](https://vitepress.dev). It is independent of the app: nothing here is imported by `sdoc/` or `web/`, and a broken docs build cannot affect the website or the API.

## Where the content comes from

| Page | Source |
|---|---|
| Home, Getting started, Categories and statuses, Privacy, Troubleshooting, API, Configuration, CLI, Run locally, Deploy on AWS | written here, in `content/` |
| User guide, Test emails, Android app, How shipdoc decides | copied from `../docs/USER-GUIDE.md`, `../docs/test-emails/README.md`, `../docs/DEMO-ANDROID.md`, `../docs/ARCHITECTURE.md` by `scripts/sync-docs.mjs` |
| Screenshots, sample `.eml` files, logo | copied from `../docs/screenshots`, `../docs/test-emails`, `../web/public` |

The copied pages are git-ignored. **Edit the source in `../docs`, not the copy.**

`scripts/sync-docs.mjs` is an **allow-list**: only the files named in it are ever published. Internal notes in `../docs` (`PLAN.md`, `TODO.md`, `HANDOFF.md`, `COMPLIANCE.md`, `AWS-DEPLOYMENT.md`) are never picked up. To publish another file, add it to `PAGES` in that script and to the sidebar in `.vitepress/config.mts`.

## Work on it

```bash
cd docs-site
npm ci
npm run dev        # live preview at http://localhost:5173
npm run build      # static site in .vitepress/dist (the build fails on a broken link, which is useful)
npm run preview    # serve the built site
```

Needs Node 20 or newer.

## Deploy

The build output is plain static files, so any static host works. The recommended setup for `docs.shipdoc.org` is **Cloudflare Pages**, because the domain's DNS is already on Cloudflare and it does not touch the main site's Amplify domain settings:

| Setting | Value |
|---|---|
| Repository | this repository, branch `main` |
| Root directory | `docs-site` |
| Build command | `npm ci && npm run build` |
| Build output directory | `.vitepress/dist` |
| Environment variable | `NODE_VERSION` = `22` |
| Custom domain | `docs.shipdoc.org` |

### On AWS Amplify instead

Create a second Amplify app from the same repository as a monorepo with app root `docs-site`, and use this build spec:

```yaml
version: 1
applications:
  - appRoot: docs-site
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: .vitepress/dist
        files:
          - '**/*'
```

Connecting `docs.shipdoc.org` to a second app whose root domain is already used by the main app needs a subdomain-only association. The Amplify console tends to try to claim the whole domain, so use the CLI:

```bash
aws amplify create-domain-association --app-id <DOCS_APP_ID> --domain-name shipdoc.org \
  --sub-domain-settings prefix=docs,branchName=main
```

## Notes

- Links use `.html` (`cleanUrls` is off) so no rewrite rules are needed on any host.
- Search is built in and works offline (local search).
- Mermaid diagrams in the Markdown render in the browser.
