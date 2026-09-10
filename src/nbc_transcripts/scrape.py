"""Fetch archived pages or parse local historical HTML into a JSONL checkpoint."""

import gzip
import json
import logging
from pathlib import Path
from urllib.parse import urlsplit

import scrapelib

from nbc_transcripts.checkpoint import prepare_checkpoint
from nbc_transcripts.parsers import parse_legacy_page

log = logging.getLogger(__name__)


def load_urls(path: Path) -> list[str]:
    """Read the historical one-path-per-line inventory."""
    return list(
        dict.fromkeys(
            line.strip()
            if line.startswith("http")
            else "http://www.nbcnews.com" + line.strip()
            for line in path.read_text().splitlines()
            if line.strip()
        )
    )


def scrape(
    urls: Path,
    out: Path,
    html_dir: Path,
    *,
    limit: int | None = None,
    local_only: bool = False,
    snapshot: str | None = None,
    session=None,
) -> dict[str, int]:
    """Append records with archive provenance and retry failures on resume."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    session = session or scrapelib.Scraper(requests_per_minute=60, retry_attempts=2)
    session.timeout = 30
    prepare_checkpoint(out)
    seen = (
        {json.loads(line)["url"] for line in out.read_text().splitlines() if line}
        if out.exists()
        else set()
    )
    counts = {"written": 0, "skipped": 0, "failed": 0}
    out.parent.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        for url in load_urls(urls):
            if url in seen:
                counts["skipped"] += 1
                continue
            if limit is not None and counts["written"] + counts["failed"] >= limit:
                break
            name = ".".join(urlsplit(url).path.strip("/").split("/")) + ".html"
            target = html_dir / (name + ".gz")
            source_url = None
            try:
                if target.exists():
                    with gzip.open(target, "rt", encoding="utf-8") as raw:
                        page = raw.read()
                elif (html_dir / name).exists():
                    page = (html_dir / name).read_text(encoding="utf-8")
                elif local_only:
                    raise FileNotFoundError(name)
                else:
                    if snapshot:
                        timestamp = snapshot
                    else:
                        data = session.get(
                            "https://archive.org/wayback/available", params={"url": url}
                        ).json()
                        closest = data.get("archived_snapshots", {}).get("closest", {})
                        if not closest.get("available"):
                            raise ValueError("no archived snapshot")
                        timestamp = closest["timestamp"]
                    source_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
                    page = session.get(source_url).text
                record = parse_legacy_page(page, url).to_record()
                if not record["text"]:
                    raise ValueError("empty archived transcript")
                part = target.with_suffix(".gz.part")
                with gzip.open(part, "wt", encoding="utf-8") as raw:
                    raw.write(page)
                part.replace(target)
                record["source_url"] = source_url
                record["html_path"] = str(target)
            except (OSError, ValueError, scrapelib.HTTPError) as exc:
                counts["failed"] += 1
                log.warning("%s: %s", url, exc)
                with (out.parent / "failures.jsonl").open("a") as failures:
                    failures.write(json.dumps({"url": url, "error": str(exc)}) + "\n")
                continue
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            seen.add(url)
            counts["written"] += 1
    return counts
