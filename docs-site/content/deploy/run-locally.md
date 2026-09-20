# Run it locally

You need **Python 3.11 or newer** for the API and **Node 20 or newer** for the dashboard. Docker is optional.

## With Docker (one command)

```bash
git clone https://github.com/VRP2206/Averis_hackathon_2026.git
cd Averis_hackathon_2026
docker compose up --build
```

| | |
|---|---|
| Dashboard | <http://localhost:5173> |
| API | <http://localhost:8000> (interactive docs at `/docs`) |

Results are kept in `./output` between restarts. Put a `.env` file next to `docker-compose.yml` to switch on an AI provider (see [Configuration](/reference/configuration)).

## Without Docker

```bash
py -3.12 -m venv .venv                 # macOS/Linux: python3 -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
sdoc serve                             # API on http://127.0.0.1:8000
```

In a second terminal:

```bash
cd web
npm install
npm run dev                            # dashboard on http://localhost:5173
```

Open the dashboard and click **Process inbox**.

## Try the pipeline without the website

```bash
sdoc run                   # process the whole inbox, write output/submission.json
sdoc inspect email_025     # one email in full: classification, checks, values, comparison
pytest -q                  # run the tests
```

More in [Command line](/reference/cli).

## Switch the AI on (optional)

With no configuration shipdoc runs on rules only. To let an AI model help with messy mail and translation, copy `.env.example` to `.env` and set a provider:

```ini
SDOC_LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

Details, and the Claude API and Amazon Bedrock options, are in [Configuration](/reference/configuration).

## Use your own emails

The dataset lives in `Provided Information/Participant Info/inbox`. You do not need it to try shipdoc on your own mail: use **Upload .eml** or **Connect mailbox** in the dashboard, or the [test emails](/guide/test-emails).

## Project layout

```text
sdoc/        the pipeline package (classify, readers, doctype, extract, compare, gate, pipeline, api, cli)
web/         the React dashboard; web/android is the Capacitor Android project
tests/       the pytest suite
docs/        project documents and screenshots
docs-site/   this documentation site
scripts/     Android demo launcher, test-email generator
apk/         prebuilt Android app
```

## Build this documentation site

```bash
cd docs-site
npm install
npm run dev        # live preview
npm run build      # static site in docs-site/.vitepress/dist
```

Several pages are copied from `docs/` by `npm run sync` (which `dev` and `build` run for you). Edit the file in `docs/`, not the copy.
