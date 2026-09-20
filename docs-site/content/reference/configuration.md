# Configuration

shipdoc is configured through environment variables. Anything starting with `SDOC_` is read into the settings object (`sdoc/config.py`). A `.env` file in the repository root works the same way; copy `.env.example` to start.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `SDOC_LLM_PROVIDER` | `none` | AI provider: `none` (rules only), `gemini`, `anthropic` or `bedrock` |
| `SDOC_USE_LLM_FOR_EXTRACTION` | `true` | Let the AI fill in fields the heuristics missed. Only used when a provider is set |
| `SDOC_EXTRACTION_MIN_CONFIDENCE` | `0.6` | Below this confidence a heuristic value is treated as missing, so the AI may fill it |
| `SDOC_LLM_CACHE_DIR` | `.cache/llm` | Where AI replies are cached by prompt hash, so reruns are free |
| `SDOC_DATA_DIR` | `Provided Information/Participant Info` | The dataset folder (an `inbox/` folder of emails and attachments) |
| `SDOC_OUTPUT_DIR` | `output` | Where `submission.json`, `results.json` and the mail cache are written |
| `SDOC_DYNAMODB_TABLE` | *(empty)* | When set, results are stored in this DynamoDB table instead of `results.json` |
| `SDOC_GROUND_TRUTH` | *(a path inside the repo)* | The organisers' scoring data for `/metrics` and `sdoc score`. It is not distributed with the repository; without it those features are simply unavailable |

## AI providers

The comparison never uses AI. The AI is used to classify an email when the rules are not confident, to fill extraction gaps, and to translate.

| Provider | Set | Models (defaults) |
|---|---|---|
| Gemini | `SDOC_LLM_PROVIDER=gemini` and `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | `SDOC_GEMINI_FAST_MODEL=gemini-2.5-flash`, `SDOC_GEMINI_STRONG_MODEL=gemini-2.5-pro` |
| Claude API | `SDOC_LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` | `SDOC_LLM_FAST_MODEL=claude-haiku-4-5-20251001`, `SDOC_LLM_STRONG_MODEL=claude-sonnet-5` |
| Amazon Bedrock | `SDOC_LLM_PROVIDER=bedrock`, `SDOC_BEDROCK_REGION`, and an IAM role with `bedrock:InvokeModel` (no API key) | `SDOC_BEDROCK_FAST_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0`, `SDOC_BEDROCK_STRONG_MODEL=us.anthropic.claude-sonnet-5-v1:0` (region default `us-east-1`) |

The *fast* model handles the first attempt; the *strong* model is only used to retry a low-confidence answer. If a provider cannot start (for example, a missing key), shipdoc logs it and carries on with rules only.

Copy the exact Bedrock inference-profile IDs from the Bedrock console for your account; the defaults are a starting point.

::: tip Check that the AI is really answering
`GET /health` only reports the configured provider. Call `POST /translate/{email_id}` and look for a real translation, with `translated: true` and an empty `note`.
:::

## Website

| Variable | Where | What it does |
|---|---|---|
| `VITE_API_URL` | the website build (`web/`) | The API address baked into the site at build time. Without it the site uses `http://127.0.0.1:8000` |

Users can override the address in the app: the gear icon stores it in the browser (this is what makes the Android app work against any server).

## Minimal examples

Rules only (the default, no keys needed):

```bash
sdoc serve
```

Gemini:

```bash
export SDOC_LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-key
sdoc serve
```

On AWS Lambda, set the same variables in the function's configuration. See [Deploy on AWS](/deploy/aws).
