"""下载馆内论文的出处数据。浏览器只读 build_data.py 生成的本地文件。"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
CURATION = ROOT / "curation"
MUSEUM = ROOT / "site" / "data" / "museum.json"
WORK_ID = re.compile(r"W[1-9][0-9]*")
OPENALEX = "https://api.openalex.org/works"
DATACITE = "https://api.datacite.org/dois"


def identifiers(exhibit: dict) -> set[str]:
    doi, arxiv = exhibit.get("doi"), exhibit.get("arxiv")
    return {
        value.lower()
        for value in (doi, f"10.48550/arxiv.{arxiv}" if arxiv else None)
        if value
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    temp.replace(path)


def get_json(url: str, query: dict) -> dict:
    address = url + "?" + urlencode(query)
    for delay in (0, 3, 9):
        time.sleep(delay)
        try:
            with urlopen(address, timeout=25) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or delay == 9:
                raise
        except (URLError, TimeoutError):
            if delay == 9:
                raise


def fetch_cached(name: str, requested: set[str], lookup, batch_size: int, retry_missing: bool) -> dict:
    path = CURATION / "cache" / "rea" / f"{name}-lookup.json"
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = sorted(key for key in requested if key not in cache or (retry_missing and cache[key] is None))
    for offset in range(0, len(todo), batch_size):
        batch = todo[offset:offset + batch_size]
        hits = lookup(batch)
        cache.update({key: hits.get(key) for key in batch})
        write_json(path, cache)
        print(f"{name}: {offset + len(batch)}/{len(todo)}", flush=True)
    return {key: cache[key] for key in sorted(requested) if cache.get(key) is not None}


def openalex_works(batch: list[str]) -> dict:
    query = {"filter": "doi:" + "|".join(batch), "select": "id,doi,referenced_works", "per_page": len(batch)}
    result = get_json(OPENALEX, query)
    if result["meta"]["count"] != len(result["results"]):
        raise ValueError("OpenAlex returned an incomplete batch")
    works = {}
    for work in result["results"]:
        doi = (work["doi"] or "").lower().removeprefix("https://doi.org/")
        wid = work["id"].removeprefix("https://openalex.org/")
        if doi in batch and WORK_ID.fullmatch(wid):
            works[doi] = {
                "work": wid,
                "references": [r.removeprefix("https://openalex.org/") for r in work["referenced_works"]],
            }
    return works


def paper_citations(exhibits: list[dict], retry_missing: bool) -> None:
    requested = set().union(*(identifiers(exhibit) for exhibit in exhibits))
    matches = fetch_cached("openalex", requested, openalex_works, 25, retry_missing)
    works = {record["work"] for record in matches.values()}
    data = {
        "provider": "OpenAlex",
        "license": "CC0-1.0",
        "identifiers": {doi: record["work"] for doi, record in matches.items()},
        "references": {
            wid: sorted({ref for record in matches.values() if record["work"] == wid
                         for ref in record["references"] if ref in works and ref != wid})
            for wid in sorted(works)
        },
    }
    write_json(CURATION / "paper_citations.json", data)
    print(f"OpenAlex: {len(matches)}/{len(requested)} identifiers, {len(works)} works, "
          f"{sum(map(len, data['references'].values()))} in-collection references")


def datacite_dates(batch: list[str]) -> dict:
    prefix = "10.48550/arxiv."
    query = "doi:(" + " OR ".join(f'"{prefix}{aid}"' for aid in batch) + ")"
    result = get_json(DATACITE, {"query": query, "fields[dois]": "doi,dates", "page[size]": len(batch)})
    if result["meta"]["total"] != len(result["data"]):
        raise ValueError("DataCite returned an incomplete batch")
    dates = {}
    for record in result["data"]:
        aid = record["id"].lower().removeprefix(prefix)
        if aid not in batch:
            continue
        submitted = {
            item["date"][:10] for item in record["attributes"]["dates"]
            if item["dateType"] == "Submitted" and item.get("dateInformation") == "v1"
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T.*Z)?", item["date"])
        }
        if len(submitted) == 1:
            dates[aid] = submitted.pop()
    return dates


def paper_dates(exhibits: list[dict], retry_missing: bool) -> None:
    arxiv = {e["arxiv"] for e in exhibits if e.get("arxiv")}
    dates = fetch_cached("datacite-v1", arxiv, datacite_dates, 25, retry_missing)
    write_json(CURATION / "paper_dates.json", {"provider": "DataCite", "arxiv_v1_submitted": dates})
    print(f"DataCite: {len(dates)}/{len(arxiv)} arXiv identifiers with v1 submission dates")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    actions = {"citations": paper_citations, "dates": paper_dates}
    parser.add_argument("dataset", choices=actions)
    parser.add_argument("--retry-missing", action="store_true", help="retry identifiers that previously returned no record")
    args = parser.parse_args()
    try:
        actions[args.dataset](json.loads(MUSEUM.read_text(encoding="utf-8"))["exhibits"], args.retry_missing)
    except HTTPError as error:
        parser.exit(1, f"Metadata request failed (HTTP {error.code}). Run the same command to resume.\n")
    except (URLError, TimeoutError, ValueError) as error:
        parser.exit(1, f"Metadata request failed ({type(error).__name__}). Run the same command to resume.\n")
