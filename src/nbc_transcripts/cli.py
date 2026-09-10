"""Historical transcript collection and conversion commands."""

import argparse
import json
import logging
import sys
from pathlib import Path

from nbc_transcripts import convert, scrape, upload


def main(argv: list[str] | None = None) -> int:
    """Run the requested command and report failures."""
    parser = argparse.ArgumentParser(prog="nbc-transcripts")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("scrape")
    command.add_argument("--urls", type=Path, default=Path("provenance/links.txt"))
    command.add_argument("--out", type=Path, default=Path("data/transcripts.jsonl"))
    command.add_argument("--html-dir", type=Path, default=Path("data/html"))
    command.add_argument("--limit", type=int)
    command.add_argument("--local-only", action="store_true")
    command.add_argument("--snapshot", help="Wayback timestamp for a known capture")
    command = sub.add_parser("to-parquet")
    command.add_argument("inputs", nargs="+", type=Path)
    command.add_argument("--out", required=True, type=Path)
    command = sub.add_parser("upload")
    command.add_argument("file", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    if args.command == "scrape":
        counts = scrape.scrape(
            args.urls,
            args.out,
            args.html_dir,
            limit=args.limit,
            local_only=args.local_only,
            snapshot=args.snapshot,
        )
        sys.stdout.write(json.dumps(counts) + "\n")
        return int(bool(counts["failed"]))
    if args.command == "to-parquet":
        rows, dropped = convert.load_records(args.inputs)
        table = convert.write_parquet(rows, args.out)
        sys.stdout.write(convert.describe(table, dropped) + "\n")
        return 0
    sys.stdout.write(upload.upload(args.file) + "\n")
    return 0
