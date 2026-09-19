"""Command line: `sdoc run | score | inspect | serve`."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import settings
from .evaluate import Evaluator, format_report
from .pipeline import build_pipeline


def cmd_run(args):
    pipe = build_pipeline(settings)
    emails = pipe.inbox.emails()
    if args.limit:
        emails = emails[: args.limit]
    results = pipe.run(emails, workers=args.workers)
    out = Path(args.out or settings.output_dir / "submission.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    sub = {eid: r.to_submission() for eid, r in sorted(results.items())}
    out.write_text(json.dumps(sub, indent=2), encoding="utf-8")
    detail = out.with_name("results_detail.json")
    detail.write_text(json.dumps([r.model_dump(mode="json") for _, r in sorted(results.items())], indent=1),
                      encoding="utf-8")
    print(f"wrote {out}  ({len(sub)} emails)  detail: {detail}")
    if not args.no_score and settings.ground_truth.exists():
        print(format_report(Evaluator(settings.ground_truth).score(sub)))


def cmd_score(args):
    sub = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    ev = Evaluator(args.ground_truth or settings.ground_truth)
    print(format_report(ev.score(sub)))
    if args.mistakes:
        for m in ev.mistakes(sub):
            print(json.dumps(m))


def cmd_inspect(args):
    pipe = build_pipeline(settings)
    r = pipe.process(pipe.inbox.get(args.email_id))
    print(json.dumps(r.model_dump(mode="json"), indent=2))


def cmd_serve(args):
    import uvicorn
    uvicorn.run("sdoc.api:app", host=args.host, port=args.port, reload=args.reload)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="sdoc", description="SDOC shipping-document pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="process the inbox and write submission.json")
    r.add_argument("--out"); r.add_argument("--limit", type=int); r.add_argument("--workers", type=int, default=8)
    r.add_argument("--no-score", action="store_true"); r.set_defaults(fn=cmd_run)

    s = sub.add_parser("score", help="score a submission against ground truth")
    s.add_argument("submission"); s.add_argument("--ground-truth"); s.add_argument("--mistakes", action="store_true")
    s.set_defaults(fn=cmd_score)

    i = sub.add_parser("inspect", help="run one email and print full detail")
    i.add_argument("email_id"); i.set_defaults(fn=cmd_inspect)

    v = sub.add_parser("serve", help="start the HTTP API")
    v.add_argument("--host", default="127.0.0.1"); v.add_argument("--port", type=int, default=8000)
    v.add_argument("--reload", action="store_true"); v.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
