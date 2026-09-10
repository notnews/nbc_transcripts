# NBC-hosted MSNBC Transcripts 2008–2014

[![CI](https://github.com/notnews/nbc_transcripts/actions/workflows/ci.yml/badge.svg)](https://github.com/notnews/nbc_transcripts/actions/workflows/ci.yml)
[![Data](https://img.shields.io/badge/data-Dataverse-blue)](https://doi.org/10.7910/DVN/ND1TCV)
[![Code license](https://img.shields.io/badge/code-MIT-green)](LICENSE)

Historical MSNBC show transcripts published on nbcnews.com. The original transcript index is defunct; this package reparses saved HTML or retrieves available Wayback snapshots from the preserved URL inventory.

## Data

| Files | Coverage | Count | DOI |
|---|---|---:|---|
| Raw HTML and parsed CSV (`msnbc-r2.csv` in the original extraction script) | 2008–2014 | 5,369 published rows, historical documentation | [ND1TCV](https://doi.org/10.7910/DVN/ND1TCV) |
| `provenance/links.txt` | Historical discovery inventory | 5,378 lines, verified locally | Same corpus |

Historical annual row counts: 2008: 76; 2009: 434; 2010: 752; 2011: 1,042; 2012: 1,164; 2013: 1,177; 2014: 724.

Counts describe the releases or local files identified above. Dataverse metadata requests returned HTTP 403 on 2026-09-10, so historical release counts could not all be reverified.

## Column dictionary

| Columns | Type | Description |
|---|---|---|
| `id`, `url` | string | Original identifier and URL; exact-URL deduplication, first input wins |
| `title`, `program` | string | Historical headline and show name |
| `aired_date`, `aired_time` | date, string | Parsed airing date and available timestamp |
| `guests`, `summary` | string | Guests when explicitly present; summary generally null |
| `text`, `wordcount` | string, int32 | Transcript and whitespace word count |
| `source` | string | Input filename |

Scrape JSONL also records the archive `source_url` for a newly fetched snapshot and local `html_path`. A local HTML file without saved fetch metadata has no asserted capture URL.

## Coverage and known gaps

The inventory has nine more lines than the historical parsed row count; this difference is not a claim that all nine are missing pages. The index contains overlapping MSNBC shows, not a census of NBC programming. This is the same legacy corpus referenced by `msnbc_transcripts`.

Known weekday and month misspellings are normalized. Incomplete dates remain null. The Wayback availability endpoint returned HTTP 429 when checked on 2026-09-10. `--snapshot TIMESTAMP` selects a known capture directly; the historical fixture snapshot remains retrievable. Unknown page layouts and empty archived transcripts fail visibly and remain eligible for retry. Original raw HTML uses filenames such as `id.38935621.ns.msnbc-rachel_maddow_show.html`.

## Collection methods

| Era | Method |
|---|---|
| 2014 | Discover paths from the NBC transcript index; parse headline, timestamp, and `div#intelliTXT` |
| From 2026-09-10 | Preserve URL inventory; parse local HTML or fetch a publicly available Wayback snapshot; append JSONL |

The historical implementation is preserved at [ab024e4f7998ba22055fadb4622365d66d0eeed3](https://github.com/notnews/nbc_transcripts/tree/ab024e4f7998ba22055fadb4622365d66d0eeed3). New fetches write checkpoints under `data/`; reruns skip successful records and retry failures. Pure parsers read saved responses without accessing the network. Fixture provenance is in [tests/fixtures/SOURCES.md](tests/fixtures/SOURCES.md).

An interrupted, unterminated final JSONL record is removed before resuming; complete records are preserved. A valid final record missing only its newline is retained. Malformed complete lines remain errors.

## Usage

Python 3.12 or later and [uv](https://docs.astral.sh/uv/) are required. Run these commands from the repository root. Keep downloaded inputs and generated files under ignored `data/`.

### Install

```sh
uv sync --frozen --group dev
```

### Collect

```sh
uv run nbc-transcripts scrape --limit 5
uv run nbc-transcripts scrape --local-only --html-dir data/html
```

### Convert

```sh
uv run nbc-transcripts to-parquet data/transcripts.jsonl --out data/transcripts.parquet
uv run nbc-transcripts to-parquet data/msnbc-r2.csv --out data/legacy.parquet
```

### Upload

The `upload` command reads `DATAVERSE_API_TOKEN` from the environment and adds the specified file to Dataverse. It does not publish a dataset version.

```sh
uv run nbc-transcripts upload data/transcripts.parquet
```

## Development

Run the local checks:

```sh
make check
```

This runs Ruff, formatting, pytest, and pre-commit. Run `make ci-docker` to check lint and tests in standard Python 3.12 and 3.14 Docker images. CI uses the same lockfile and checks. Install the Git hooks with `uv run pre-commit install`.

## Citation

Use [CITATION.cff](CITATION.cff) and cite the relevant [Dataverse release](https://doi.org/10.7910/DVN/ND1TCV), including its version and DOI.

## License

Code is [MIT licensed](LICENSE). News text, abstracts, and archived pages retain their owners' rights; a code license does not grant rights to those materials. The [Dataverse DOI record](https://api.datacite.org/dois/10.7910/DVN/ND1TCV) specifies CC0 1.0 for the deposit. Consult the release for access conditions.

## Adjacent Repositories

- [notnews/fox_news_transcripts](https://github.com/notnews/fox_news_transcripts) — Fox News Transcripts 2003--2025
- [notnews/cnn_transcripts](https://github.com/notnews/cnn_transcripts) — CNN Transcripts 2000--2025
- [notnews/stanford_tv_news](https://github.com/notnews/stanford_tv_news) — Stanford Cable TV News Dataset
- [notnews/lacc_to_csv](https://github.com/notnews/lacc_to_csv) — Los Angeles Closed-Caption Television News Archive Data to CSV
- [notnews/archive_news_cc](https://github.com/notnews/archive_news_cc) — Closed Caption Transcripts of News Videos from archive.org 2014--2023
