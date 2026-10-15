# Self-hosting on a homelab (Docker + Caddy + Cloudflare Tunnel)

Runs shipdoc on a home server instead of AWS. Public traffic: Cloudflare -> tunnel -> Caddy (:80) -> app ports.

1. In the repo root, create `.env` with `SDOC_LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...`,
   `SDOC_ALLOWED_ORIGINS=*` and `VITE_API_URL=https://lab-api.shipdoc.org`, then `docker compose up -d --build`
   (site on :5173, API on :8000, results kept in `./output`).
2. In this folder, copy `.env.example` to `.env` and set `TUNNEL_TOKEN` (Cloudflare Zero Trust -> Tunnels), then `docker compose up -d`.
3. Tunnel public hostnames: `lab.shipdoc.org` and `lab-api.shipdoc.org`, both service **HTTP** `localhost:80`
   (Caddy routes by hostname, see `Caddyfile`; add one block per extra deployment).
4. DNS: proxied CNAMEs for each hostname to `<tunnel-id>.cfargotunnel.com`.

Never commit `.env` (tunnel token, Gemini key).
