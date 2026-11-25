"""注意力博物馆的一键检查：重新生成数据，再核对数据和页面。上线前和每次更新后都跑。

用法：python check.py        全部通过时退出码为 0
每一项检查对应一类真实会出的错，失败时打印出错的条目。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
sys.path.insert(0, str(HERE))
import build_data as bd  # noqa: E402
from fetch_paper_metadata import WORK_ID, identifiers  # noqa: E402

failures: list[str] = []


def check(name: str, bad: list) -> None:
    if bad:
        failures.append(name)
        print(f"FAIL {name}：{len(bad)} 处")
        for b in bad[:10]:
            print("     ", b)
    else:
        print(f"ok   {name}")


def english_cjk(data: dict) -> list[str]:
    """列出英文模式会显示、却含中日韩字符的数据字段。范围和 app.js 英文模式取的字段一致。"""
    bad = []

    def look(where: str, field: str, v) -> None:
        if isinstance(v, str) and bd.CJK.search(v):
            bad.append(f"{where} {field}: {v[:60]}")

    for e in data["exhibits"]:
        look(e["id"], "name_en", e["name_en"])
        for k, v in e.get("en", {}).items():
            look(e["id"], f"en.{k}", v)
        for k in ("fig_no", "caption"):
            look(e["id"], f"figure.{k}", (e.get("figure") or {}).get(k))
        for k in ("repo", "commit", "arxiv", "doi"):
            look(e["id"], k, e.get(k))
        for i, c in enumerate(e["copies"]):
            for k, v in c.get("en", {}).items():
                look(e["id"], f"copies[{i}].en.{k}", v)
            for k in ("repo", "commit"):
                look(e["id"], f"copies[{i}].{k}", c.get(k))
            for fn in c.get("code_files", []):
                look(e["id"], f"copies[{i}].code_files", fn)
    for g in data["edges"]:
        look(f"{g['source']}→{g['target']}", "evidence_en", g.get("evidence_en"))
    for n in data["graph"]["nodes"]:
        look(n["id"], "label" if n["kind"] == "exhibit" else "label_en", n["label"] if n["kind"] == "exhibit" else n.get("label_en"))
    for h in data["halls"]["fields"]:
        look(h["field"], "en", h.get("en") or h["field"])
        for tk in h["tasks"]:
            look(tk["task"], "en", tk.get("en") or tk["task"])
    for k, d in data["directions"].items():
        look(f"方向 {k}", "en", d.get("en") or d["zh"])
    for s in data["census"]["skipped"] + data["census"]["no_official_code"]:
        look("统计页", "name", s["name"])
    story = data.get("story") or {}
    look("导览", "thesis_en", story.get("thesis_en"))
    for c in story.get("chapters", []):
        for k in ("title_en", "lede_en", "body_en"):
            look(f"导览 {c.get('id')}", k, c.get(k))
        for a in c.get("anchors", []):
            look(f"导览 {c.get('id')}/{a.get('id')}", "note_en", a.get("note_en"))
    return bad


def citation_errors(data: dict) -> list:
    graph = data["citation_graph"]
    works = graph["works"]
    curation = bd.load_curation_json(bd.CURATION / "paper_citations.json")
    lookup = curation.get("identifiers", {})
    refs = curation.get("references", {})
    exhibits = {e["id"]: e for e in data["exhibits"]}
    bad = []
    seen = Counter(graph["unmatched"].keys())
    for work, members in works.items():
        if not WORK_ID.fullmatch(work) or work not in refs or not members:
            bad.append(work)
        seen.update(members)
        for exhibit_id in members:
            ids = identifiers(exhibits.get(exhibit_id, {}))
            if {lookup[key] for key in ids if key in lookup} != {work}:
                bad.append((work, exhibit_id))
    for exhibit_id, reason in graph["unmatched"].items():
        ids = identifiers(exhibits.get(exhibit_id, {}))
        hits = {lookup[key] for key in ids if key in lookup}
        expected = "ambiguous" if len(hits) > 1 else "unresolved" if ids else "no_identifier"
        if len(hits) == 1 or reason != expected:
            bad.append((exhibit_id, reason))
    actual = Counter((edge["citing"], edge["cited"]) for edge in graph["edges"])
    expected = {(work, ref) for work in works for ref in refs.get(work, []) if ref in works and work != ref}
    bad.extend(pair for pair in actual.keys() | expected if actual[pair] != (pair in expected))
    for edge in graph["edges"]:
        url = f"https://api.openalex.org/works/{edge['citing']}?select=id,referenced_works"
        if edge["source_url"] != url:
            bad.append(edge["source_url"])
    bad.extend(exhibit_id for exhibit_id in seen.keys() | exhibits.keys()
               if seen[exhibit_id] != (exhibit_id in exhibits))
    if (bd.CURATION / "paper_citations.json").exists() and (
        curation.get("provider"), curation.get("license")
    ) != ("OpenAlex", "CC0-1.0"):
        bad.append("OpenAlex / CC0-1.0")
    return bad


def paper_date_errors(data: dict) -> list:
    path = bd.CURATION / "paper_dates.json"
    source = bd.load_curation_json(path)
    dates = source.get("arxiv_v1_submitted", {})
    arxiv = {e["arxiv"] for e in data["exhibits"] if e.get("arxiv")}
    emitted = data["paper_dates"]
    bad = sorted(emitted.keys() ^ (dates.keys() & arxiv))
    if path.exists() and source.get("provider") != "DataCite":
        bad.append("DataCite")
    for aid, row in emitted.items():
        try:
            day = date.fromisoformat(row["date"]).isoformat()
        except (ValueError, TypeError):
            day = None
        if (not day or day != dates.get(aid) or not re.fullmatch(r"\d{4}\.\d{4,5}", aid)
                or row["kind"] != "arxiv_v1_submitted"
                or row["source_url"] != f"https://arxiv.org/abs/{aid}v1"
                or row["metadata_url"] != f"https://api.datacite.org/dois/10.48550/arxiv.{aid}"):
            bad.append(aid)
    return bad


def mask_errors() -> list:
    js = """
      import assert from "node:assert/strict";
      import { canSee, maskWeights, positions } from "./prototypes/mask/model.mjs";
      for (const [query, mode, size, expected] of [
        [0, "causal", 3, [0]],
        [4, "causal", 3, [0, 1, 2, 3, 4]],
        [4, "window", 3, [2, 3, 4]],
        [7, "window", 1, [7]],
        [4, "full", 3, [0, 1, 2, 3, 4, 5, 6, 7]],
      ]) {
        const visible = Array.from({ length: positions }, (_, i) => i)
          .filter(i => canSee(query, i, mode, size));
        assert.deepEqual(visible, expected);
        const row = maskWeights(query, mode, size);
        const sum = expected.reduce((total, key) => total + Math.exp(row[key].score), 0);
        row.forEach(({ score, weight }, key) => {
          const correct = expected.includes(key) ? Math.exp(score) / sum : 0;
          assert.ok(Math.abs(weight - correct) < 1e-12);
        });
      }
    """
    r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=HERE,
                       capture_output=True, encoding="utf-8")
    return r.stderr.splitlines() if r.returncode else []


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sources = [bd.INDEX, bd.QUEUE, bd.REPRO_QUEUE, bd.VERIFY_LOG, bd.EXTEND_LOG]
    stamp = [f.stat().st_mtime for f in sources]      # 收集会话可能同时在写这些文件
    r = subprocess.run([sys.executable, str(HERE / "build_data.py")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        return 1
    data = json.loads((SITE / "data" / "museum.json").read_text(encoding="utf-8"))
    code = json.loads((SITE / "data" / "code.json").read_text(encoding="utf-8"))
    ex = data["exhibits"]
    ids = [e["id"] for e in ex]

    # 1. 展品编号唯一，页面靠它定位展品
    check("展品编号唯一", [k for k, n in Counter(ids).items() if n > 1])

    # 2. 队列的每一行恰好归到一件展品：防止归并规则吃掉或重复计入队列行
    ext = bd.load_extend_log()
    rows = [(q["queue"], q["no"]) for q in bd.load_queue(ext) + bd.load_repro_queue(ext)]
    seen = Counter((r["queue"], r["no"]) for e in ex for r in e["queue"])
    check("队列行恰好归入一件展品", [r for r in rows if seen[r] != 1] + [r for r in seen if r not in set(rows)])

    # 3. INDEX 里模块类型含「注意力」的目录都有馆藏副本：防止漏收
    held = {c["path"] for e in ex for c in e["copies"]}
    check("INDEX 的注意力模块都已入馆", [r["path"] for r in bd.load_index() if "注意力" in r["module_type"] and r["path"] not in held])

    # 4. 谱系边和图谱边的两端都存在
    idset = set(ids)
    check("谱系边两端都是展品", [g for g in data["edges"] if g["source"] not in idset or g["target"] not in idset])
    gids = {n["id"] for n in data["graph"]["nodes"]}
    check("图谱边两端都存在", [l for l in data["graph"]["links"] if l["source"] not in gids or l["target"] not in gids])
    check("馆内引用方向、论文标识和出处一致", citation_errors(data))
    check("首次提交日的论文编号、日期和出处一致", paper_date_errors(data))
    check("注意力掩码方向和权重正确", mask_errors())

    # 5. 只展示照论文复现的自写代码：别人仓库的代码有约 40 个没有明确许可证
    repro_paths = {c["path"] for e in ex for c in e["copies"] if c["source_type"] == "repro"}
    check("code.json 只含照论文复现的代码", [p for p in code if p not in repro_paths or "论文复现" not in p.split("/")[-1] and p not in repro_paths])

    # 6. 「缺」的标记和字段实际取值一致：页面上写缺的必须真的为空
    bad = []
    for e in ex:
        for k in e["missing"]:
            if k != "paper_link" and e.get(k):
                bad.append((e["id"], k))
    check("缺字段标记与取值一致", bad)

    # 7. 页面不从外部域名加载资源：国内访问不了 Google Fonts 等，也不把访客信息交给第三方
    ext_refs = []
    prototypes = sorted(f for f in (HERE / "prototypes").rglob("*") if f.suffix in (".html", ".js", ".mjs", ".css"))
    for f in [SITE / "index.html", *sorted((SITE / "assets").glob("*.css")), *sorted((SITE / "assets").glob("*.js")), SITE / "assets" / "fonts" / "fonts.css", *prototypes]:
        t = f.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:src=|href=|url\(|@import\s+)["\']?(https?:)?//[^"\')\s]+', t):
            if f.suffix == ".html" and "<a " in t[max(0, m.start() - 40):m.start()]:
                continue
            ext_refs.append(f"{f.relative_to(HERE)}: {m.group(0)[:80]}")
        if f in prototypes and re.search(r"""(?:fetch\(|import\s+.*?from\s+|@import\s*)\s*["'](?:https?:)?//""", t):
            ext_refs.append(f"{f.relative_to(HERE)}: external request")
    check("不从外部域名加载资源", ext_refs)

    # 8. index.html 引用的本地文件都存在
    html = (SITE / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="(assets/[^"#?]+)', html) + ["data/museum.json", "data/code.json", "assets/vendor/graph3d.min.js", "assets/rose.svg", "assets/overview.js", "assets/overview.css", "assets/frame-light.svg", "assets/frame-dark.svg"]
    check("引用的本地文件都存在", [p for p in refs if not (SITE / p).exists()])

    # 9. 中英文案的键一致：切换语言时不出现空白
    app = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
    graph = (SITE / "assets" / "graph.js").read_text(encoding="utf-8")
    decl = re.search(r"const I18N = \{.*?\n\};", app, re.S).group(0)
    assigns = "\n".join(re.findall(r"Object\.assign\(I18N\.(?:zh|en), \{.*?\n\}\);", graph, re.S))
    js = decl + "\n" + assigns + """
      const flat = (o, p = "") => Object.entries(o).flatMap(([k, v]) =>
        v && typeof v === "object" ? flat(v, p + k + ".") : [p + k]);
      const zh = new Set(flat(I18N.zh)), en = new Set(flat(I18N.en));
      const vals = (o, p = "") => Object.entries(o).flatMap(([k, v]) => {
        if (typeof v === "function") { try { v = v({ fig_no: "Figure 1" }, 2, 3); } catch (e) { v = String(e); } }
        return v && typeof v === "object" ? vals(v, p + k + ".") : [[p + k, String(v)]];
      });
      const cjk = vals(I18N.en).filter(([k, v]) => /[\\u3000-\\u303f\\u3400-\\u9fff\\uff00-\\uffef]/.test(v)).map(([k, v]) => k + ": " + v);
      console.log(JSON.stringify({ keys: [...zh].filter(k => !en.has(k)).concat([...en].filter(k => !zh.has(k))), cjk }));"""
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    res = {"keys": [r.stderr.strip()], "cjk": [r.stderr.strip()]} if r.returncode else json.loads(r.stdout)
    check("中英文案的键一致", res["keys"])

    # 11. museum.json 引用的论文图都在 site/ 下：配图会话边下载边写 figures.json，文件可能没到
    check("引用的论文图文件都存在", [f"{e['id']}: {e['figure']['file']}" for e in ex if e.get("figure") and not (SITE / e["figure"]["file"]).is_file()])

    # 12. 英文模式显示的文字里没有中日韩字符：切到英文后不该再看到中文
    check("英文模式显示的字段没有中文", res["cjk"] + english_cjk(data))

    # 13. 导览稿点名的展品都在馆内：展品编号随年份和名字生成，改名后导览会指向不存在的展品
    chapters = (data.get("story") or {}).get("chapters", [])
    check("导览的代表展品都在馆内", [f"{c.get('id')}: {a.get('id')}" for c in chapters for a in c.get("anchors", []) if a.get("id") not in idset])

    # 10. 关于页写的第三方版本和实际打包的一致：升级依赖时容易忘改页面
    deps = json.loads((HERE / "vendor-build" / "package.json").read_text(encoding="utf-8"))["dependencies"]
    check("关于页的第三方版本与打包一致",
          [f"{k} {v}" for k, v in deps.items() if k in ("3d-force-graph", "three") and f"{'three.js' if k == 'three' else k} {v}" not in app])
    vendor = SITE / "assets" / "vendor"
    lock = json.loads((HERE / "vendor-build" / "package-lock.json").read_text(encoding="utf-8"))
    viewer = lock["packages"].get("node_modules/openseadragon", {})
    versions = (vendor / "VERSIONS.txt").read_text(encoding="utf-8").splitlines()
    check("论文图查看器的版本、产物和许可证齐全", [
        name for name, valid in {
            "openseadragon": bool(re.fullmatch(r"\d+\.\d+\.\d+", deps.get("openseadragon", "")))
            and viewer.get("version") == deps["openseadragon"]
            and f"openseadragon {deps['openseadragon']}" in versions,
            "BSD-3-Clause": viewer.get("license") == "BSD-3-Clause",
            "openseadragon.min.js": (vendor / "openseadragon.min.js").is_file(),
            "LICENSE-OpenSeadragon.txt": (vendor / "LICENSE-OpenSeadragon.txt").is_file(),
        }.items() if not valid
    ])

    print()
    if failures and stamp != [f.stat().st_mtime for f in sources]:
        print("检查期间收集会话改了 INDEX 或队列文件，上面的失败可能是这个原因。请重跑一次。")
        return 2
    print("全部通过" if not failures else f"{len(failures)} 项没有通过：{'、'.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
