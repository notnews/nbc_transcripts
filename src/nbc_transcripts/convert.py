"""Convert legacy CSV or parsed JSONL into typed Parquet."""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = pa.schema(
    [
        pa.field("id", pa.string(), nullable=False),
        pa.field("url", pa.string(), nullable=False),
        pa.field("title", pa.string()),
        pa.field("program", pa.string()),
        pa.field("aired_date", pa.date32()),
        pa.field("aired_time", pa.string()),
        pa.field("guests", pa.string()),
        pa.field("summary", pa.string()),
        pa.field("text", pa.string()),
        pa.field("wordcount", pa.int32()),
        pa.field("source", pa.string(), nullable=False),
    ]
)

csv.field_size_limit(sys.maxsize)


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _iso_date(value: str | None) -> date | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _iso_time(value: str | None) -> str | None:
    value = _blank_to_none(value)
    if value is None or "T" not in value:
        return None
    return value.split("T", 1)[1][:5]


def _strip_guests(value: str | None) -> str | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    lowered = value.lower()
    if lowered.startswith(("guests:", "guest:")):
        value = value.split(":", 1)[1]
    return value.strip(" ,") or None


def rows_from_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a scrape checkpoint into schema-shaped records."""
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            records.append(
                {
                    "id": str(row["id"]),
                    "url": row["url"],
                    "title": row.get("title"),
                    "program": row.get("program"),
                    "aired_date": _iso_date(row.get("aired_date")),
                    "aired_time": row.get("aired_time"),
                    "guests": row.get("guests"),
                    "summary": row.get("summary"),
                    "text": row.get("text") or "",
                    "wordcount": row.get("wordcount") or 0,
                    "source": path.name,
                }
            )
    return records


def rows_from_listing_csv(path: Path) -> list[dict[str, Any]]:
    """Read the 2025 listing-page scrape CSV."""
    records = []
    with (
        gzip.open(path, "rt", encoding="utf-8", newline="")
        if path.suffix == ".gz"
        else path.open(encoding="utf-8", newline="")
    ) as handle:
        for row in csv.DictReader(handle):
            url = _blank_to_none(row.get("url"))
            if url is None:
                continue
            text = _blank_to_none(row.get("text"))
            aired = _iso_date(row.get("air_date"))
            if row.get("year") and row.get("month") and row.get("date"):
                try:
                    aired = date(int(row["year"]), int(row["month"]), int(row["date"]))
                except ValueError:
                    aired = _iso_date(row.get("air_date"))
            records.append(
                {
                    "id": _blank_to_none(row.get("uid"))
                    or url.rstrip("/").rsplit("/", 1)[-1],
                    "url": url,
                    "title": _blank_to_none(row.get("headline") or row.get("subhead")),
                    "program": _blank_to_none(
                        row.get("show_name") or row.get("program.name")
                    ),
                    "aired_date": aired,
                    "aired_time": _blank_to_none(row.get("time")),
                    "guests": _strip_guests(row.get("guests")),
                    "summary": _blank_to_none(row.get("summary")),
                    "text": text,
                    "wordcount": len(text.split()) if text is not None else None,
                    "source": path.name,
                }
            )
    return records


def load_records(paths: list[Path]) -> tuple[list[dict[str, Any]], int]:
    """Read every input in order, dropping repeats of a URL seen earlier.

    Args:
        paths: JSONL checkpoints and CSVs, see the module docstring.
        html_dir: Directory of ``{id}.html.gz`` files for the API metadata CSV.

    Returns:
        Kept records and the number of duplicate URLs dropped.
    """
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    dropped = 0
    for path in paths:
        if path.suffix == ".jsonl":
            rows = rows_from_jsonl(path)
        else:
            rows = rows_from_listing_csv(path)
        for record in rows:
            if record["url"] in seen:
                dropped += 1
                continue
            seen.add(record["url"])
            kept.append(record)
    return kept, dropped


def write_parquet(records: list[dict[str, Any]], out: Path) -> pa.Table:
    """Write records sorted by air date under :data:`SCHEMA`."""
    records = sorted(
        records, key=lambda r: (r["aired_date"] is None, r["aired_date"] or date.min)
    )
    table = pa.Table.from_pylist(records, schema=SCHEMA)
    out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out, compression="zstd", row_group_size=20_000)
    return table


def describe(table: pa.Table, dropped: int) -> str:
    """Rows per source, duplicates dropped, rows per year, empty transcripts."""
    lines = [f"rows: {table.num_rows}  duplicates dropped: {dropped}", "per source:"]
    lines.extend(
        f"  {name}: {count}"
        for name, count in sorted(Counter(table.column("source").to_pylist()).items())
    )
    years = Counter(
        d.year if d else None for d in table.column("aired_date").to_pylist()
    )
    lines.append("per year:")
    lines.extend(
        f"  {year or 'missing'}: {count}"
        for year, count in sorted(
            years.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)
        )
    )
    empty = sum(1 for n in table.column("wordcount").to_pylist() if not n)
    lines.append(f"empty transcripts: {empty}")
    return "\n".join(lines)
