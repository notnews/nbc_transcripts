import gzip
import json
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from nbc_transcripts import cli, convert, parsers, scrape

PAGE = (Path(__file__).parent / "fixtures/legacy.html").read_text()
URL = "http://www.nbcnews.com/id/38935621/ns/msnbc-rachel_maddow_show/"


def test_legacy_parser():
    row = parsers.parse_legacy_page(PAGE, URL)
    assert row.id == "38935621"
    assert row.aired_date == date(2010, 8, 30)
    assert row.text
    assert "Copyright 2010" not in row.text
    assert parsers.parse_legacy_date("Februrary 3, 2011") == date(2011, 2, 3)
    assert parsers.parse_legacy_date("February") is None
    with pytest.raises(ValueError, match="layout"):
        parsers.parse_legacy_page("<html>Unavailable</html>", URL)


def test_local_scrape_resume_and_convert(tmp_path):
    urls = tmp_path / "urls.txt"
    urls.write_text(URL + "\n")
    html = tmp_path / "html"
    html.mkdir()
    (html / "id.38935621.ns.msnbc-rachel_maddow_show.html").write_text(PAGE)
    out = tmp_path / "transcripts.jsonl"
    assert scrape.scrape(urls, out, html, local_only=True)["written"] == 1
    assert scrape.scrape(urls, out, html, local_only=True)["skipped"] == 1
    assert json.loads(out.read_text())["id"] == "38935621"
    parquet = tmp_path / "out.parquet"
    assert cli.main(["to-parquet", str(out), "--out", str(parquet)]) == 0
    assert pq.read_table(parquet).schema == convert.SCHEMA


def test_legacy_compressed_csv(tmp_path):
    path = tmp_path / "legacy.csv.gz"
    with gzip.open(path, "wt") as handle:
        handle.write(
            "url,program.name,year,month,date,text\n"
            "https://example.com/a,Maddow,2011,2,3,one two\n"
        )
    rows, dropped = convert.load_records([path])
    assert dropped == 0
    assert rows[0]["program"] == "Maddow"
    assert rows[0]["aired_date"] == date(2011, 2, 3)
