"""取馆内全部 arXiv 论文的题目和摘要，存到 curation/cache/arxiv_meta.json。馆长重写机制句时用。

用法：python fetch_arxiv_meta.py     已取过的编号跳过，可以反复运行
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "curation" / "cache" / "arxiv_meta.json"
NS = {"a": "http://www.w3.org/2005/Atom"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ex = json.loads((HERE / "site" / "data" / "museum.json").read_text(encoding="utf-8"))["exhibits"]
    ids = sorted({e["arxiv"] for e in ex if e.get("arxiv")})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    meta = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [i for i in ids if i not in meta]
    for k in range(0, len(todo), 80):
        batch = todo[k:k + 80]
        url = "http://export.arxiv.org/api/query?max_results=100&id_list=" + ",".join(batch)
        for wait in (0, 30, 90, 240):          # arXiv 接口限流时返回 429 或 503，等一会儿再取
            time.sleep(wait)
            try:
                with urllib.request.urlopen(url, timeout=90) as r:
                    root = ET.fromstring(r.read())
                break
            except urllib.error.HTTPError as err:
                if err.code not in (429, 503) or wait == 240:
                    raise
        for ent in root.findall("a:entry", NS):
            aid = re.sub(r"v\d+$", "", ent.findtext("a:id", "", NS).rsplit("/abs/", 1)[-1])
            meta[aid] = {
                "title": " ".join(ent.findtext("a:title", "", NS).split()),
                "abstract": " ".join(ent.findtext("a:summary", "", NS).split()),
                "published": ent.findtext("a:published", "", NS)[:10],
            }
        OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{min(k + 80, len(todo))}/{len(todo)}")
        time.sleep(3)
    print(f"共 {len(ids)} 个编号，已有摘要 {sum(1 for i in ids if i in meta)} 个，缺 {[i for i in ids if i not in meta][:20]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
