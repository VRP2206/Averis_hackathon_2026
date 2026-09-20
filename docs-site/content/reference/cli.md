# Command line

Installing the project (`pip install -e ".[dev]"`) adds the `sdoc` command.

## `sdoc run`

Processes the whole inbox and writes `output/submission.json` (or the path you give). If the organisers' scoring data is present it prints the score too.

```bash
sdoc run
sdoc run --out my-submission.json --workers 8
sdoc run --limit 50          # only the first 50 emails
sdoc run --no-score          # do not score, even if scoring data exists
```

## `sdoc score`

Scores a submission file against the organisers' scoring data (which you need to have) and prints the breakdown.

```bash
sdoc score output/submission.json
sdoc score output/submission.json --mistakes     # list every wrong answer
sdoc score output/submission.json --ground-truth path/to/scoring-data.json
```

## `sdoc inspect`

Runs one email and prints everything: classification, each check, extractions with their source lines, comparisons and the drafted reply.

```bash
sdoc inspect email_025
```

## `sdoc serve`

Starts the [HTTP API](/reference/api) (FastAPI on uvicorn).

```bash
sdoc serve                          # http://127.0.0.1:8000
sdoc serve --host 0.0.0.0 --port 8000
sdoc serve --reload                 # restart on code changes
```

Interactive API docs are then at `http://127.0.0.1:8000/docs`.

## Tests

```bash
pytest -q
```

The tests cover the classifier, readers and extraction, comparison, the pipeline and API, the mail parser, and the AWS pieces (DynamoDB store and the Lambda handler).
