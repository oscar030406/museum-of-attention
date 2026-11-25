# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "pillow",
#     "resvg-py>=0.5.0",
# ]
# ///
"""给每件有 arXiv 编号的展品取论文里的模块结构图，存到 site/figures/。

用法：uv run --script fetch_figures.py [--only 编号,编号] [--no-download]
可以反复运行：已解析的论文、已下载且没换选的图都跳过。

流程：
1. 每篇论文取网页版 arxiv.org/html/<编号>，没有图再取 ar5iv.labs.arxiv.org/html/<编号>，
   两处都没有图时取 arxiv.org/e-print/<编号> 的 LaTeX 源码包。全部候选图写进
   curation/cache/figure_candidates.json。
2. 许可证从 export.arxiv.org/abs/<编号> 读（和 arxiv.org/abs 同一页面，主机分开，可以并行）。
3. 按题注给每件展品打分选图。curation/figures_override.json 的 {展品id: 候选序号} 优先，
   值为 null 表示该论文没有合适的结构图，不填。
4. 下载入选图，SVG 先用 resvg 渲染成位图，宽度超过 1000 px 的缩到 1000 px，转 webp，写 curation/figures.json。

访问频率：同一主机 3 秒一次请求，遇到 429/503 等待后重试。
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image
import resvg_py

HERE = Path(__file__).resolve().parent
CUR = HERE / "curation"
CACHE = CUR / "cache"
PAGES = CACHE / "pages"
EPRINT = CACHE / "eprint"
CAND_F = CACHE / "figure_candidates.json"
DL_F = CACHE / "downloaded.json"
FIG_F = CUR / "figures.json"
OVR_F = CUR / "figures_override.json"
FIG_DIR = HERE / "site" / "figures"
UA = "Mozilla/5.0 (compatible; paper-figure-fetcher/1.0)"
MAX_W = 1000
TARGET_BYTES = 300_000
EPRINT_MAX = 80_000_000
PDFTOPPM = shutil.which("pdftoppm")

# ---------------------------------------------------------------- 网络


class Host:
    def __init__(self, gap: float = 3.0):
        self.gap = gap
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self, extra: float = 0.0):
        with self.lock:
            now = time.time()
            if extra:
                self.next = max(self.next, now + extra)
            if self.next > now:
                time.sleep(self.next - now)
            self.next = time.time() + self.gap


HOSTS: dict[str, Host] = {}
HOSTS_LOCK = threading.Lock()


def host_of(url: str) -> Host:
    h = urllib.parse.urlparse(url).netloc
    with HOSTS_LOCK:
        return HOSTS.setdefault(h, Host())


def get(url: str, limit: int | None = None) -> tuple[int, bytes, str, str]:
    """返回 (状态码, 内容, 最终地址, Content-Type)。404/410 正常返回，429/503/网络错误等待重试。"""
    host = host_of(url)
    extra = 0.0
    for attempt in range(6):
        host.wait(extra)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read(limit + 1) if limit else r.read()
                return r.status, data, r.geturl(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410, 400, 403):
                return e.code, b"", url, ""
            if e.code not in (429, 500, 502, 503, 504):
                raise
            ra = e.headers.get("Retry-After") if e.headers else None
            extra = float(ra) if ra and ra.isdigit() else 30 * (attempt + 1) ** 2
            print(f"  {e.code} {url}，等 {extra:.0f} 秒", flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            extra = 20 * (attempt + 1)
            print(f"  网络错误 {e} {url}，等 {extra} 秒", flush=True)
    raise RuntimeError(f"多次重试失败：{url}")


# ---------------------------------------------------------------- 解析网页版


def clean_text(node: Tag) -> str:
    node = BeautifulSoup(str(node), "html.parser")
    for m in node.find_all("math"):
        alt = m.get("alttext")
        m.replace_with(f"${alt}$" if alt else m.get_text(" "))
    for c in node.find_all("cite"):
        c.replace_with("[" + c.get_text("").strip("[]") + "]")
    return re.sub(r"\s+", " ", node.get_text(" ")).replace(" ,", ",").replace(" .", ".").strip()


def figure_cand(fig: Tag, cap: Tag | None, base: str) -> dict | None:
    fig_no, caption = "", ""
    if cap:
        tag = cap.find(class_="ltx_tag")
        if tag:
            fig_no = re.sub(r"[\s:.|$]+$", "", tag.get_text(" ").strip())
            tag.extract()
        caption = clean_text(cap)
    panels, row = [], 0
    for el in fig.find_all(["img", "object", "div"]):
        ecls = el.get("class") or []
        if el.name == "div":
            if "ltx_flex_break" in ecls:
                row += 1
            continue
        if "ltx_graphics" not in ecls:
            continue
        src = el.get("src") if el.name == "img" else el.get("data")
        if not src:
            continue
        w, h = int(float(el.get("width") or 0)), int(float(el.get("height") or 0))
        panels.append({"img": urllib.parse.urljoin(base, src), "w": w, "h": h, "row": row})
    has_svg = fig.find("svg") is not None
    if not panels and not has_svg:
        return None
    best = max(panels, key=lambda p: p["w"] * p["h"]) if panels else None
    # 内嵌 SVG（TikZ）取不下来：只有它时不可用；和位图混排时拼出来会缺子图，也不可用
    kind = "img" if panels and not has_svg else ("mixed" if panels else "inline-svg")
    return {
        "fig_no": fig_no, "caption": caption,
        "img": best["img"] if best else None,
        "w": best["w"] if best else 0, "h": best["h"] if best else 0,
        "n_panels": len(panels), "kind": kind, "panels": panels,
        "html_id": fig.get("id"),
    }


def top_figures(soup: BeautifulSoup):
    for fig in soup.find_all("figure"):
        cls = fig.get("class") or []
        if "ltx_figure" not in cls or "ltx_figure_panel" in cls:
            continue
        if fig.find_parent("figure", class_="ltx_figure"):
            continue
        yield fig


def parse_html(html: bytes, base: str) -> list[dict]:
    out = []
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("base", href=True)
    if tag:  # 少数页面用 <base href> 指定图片目录
        base = urllib.parse.urljoin(base, tag["href"])
    for fig in top_figures(soup):
        c = figure_cand(fig, fig.find("figcaption", recursive=False) or fig.find("figcaption"), base)
        if c:
            out.append(c)
    for i, c in enumerate(out):
        c["idx"] = i
    return out


def cached_page(aid: str, tag: str, url: str) -> tuple[bytes | None, str]:
    p = PAGES / f"{aid}.{tag}.html.gz"
    meta = PAGES / f"{aid}.{tag}.url"
    if p.exists():
        return gzip.decompress(p.read_bytes()) or None, meta.read_text(encoding="utf-8")
    st, data, final, _ = get(url)
    ok = st == 200 and b"ltx_document" in data
    final_host = urllib.parse.urlparse(final).netloc
    if ok and final_host != urllib.parse.urlparse(url).netloc:
        ok = False  # ar5iv 跳回 arxiv.org/abs 等
    p.write_bytes(gzip.compress(data if ok else b""))
    meta.write_text(final, encoding="utf-8")
    return (data if ok else None), final


# ---------------------------------------------------------------- 源码包


def brace_arg(s: str, i: int) -> tuple[str, int]:
    """s[i] 应为 '{'，返回括号内文本和结束位置。"""
    while i < len(s) and s[i] in " \t\n[":
        if s[i] == "[":
            i = s.index("]", i) + 1
        else:
            i += 1
    if i >= len(s) or s[i] != "{":
        return "", i
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{" and s[j - 1] != "\\":
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def tex_to_text(t: str) -> str:
    t = re.sub(r"(?<!\\)%.*", "", t)
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = re.sub(r"\\(cite[tp]?|ref|eqref|autoref|cref|Cref)\{[^}]*\}", "[ref]", t)
    for _ in range(3):
        t = re.sub(r"\\(textbf|textit|emph|texttt|textsc|mathrm|mathbf|text|textrm|underline|small|footnotesize)\{([^{}]*)\}", r"\2", t)
    t = re.sub(r"\\(small|footnotesize|centering|bf|it|scriptsize|vspace\{[^}]*\}|hspace\{[^}]*\})", "", t)
    t = t.replace("~", " ").replace("\\\\", " ")
    return re.sub(r"\s+", " ", t).strip()


def expand_tex(root: Path, f: Path, seen: set) -> str:
    if f in seen or not f.exists():
        return ""
    seen.add(f)
    s = f.read_text(encoding="utf-8", errors="ignore")
    s = re.sub(r"(?<!\\)%.*", "", s)

    def rep(m):
        name = m.group(2).strip()
        cand = [root / name, root / (name + ".tex"), f.parent / name, f.parent / (name + ".tex")]
        for c in cand:
            if c.is_file():
                return expand_tex(root, c, seen)
        return ""
    return re.sub(r"\\(input|include|subfile)\{([^}]*)\}", rep, s)


def find_graphic(root: Path, name: str, gpaths: list[str]) -> Path | None:
    name = name.strip().strip('"')
    exts = ["", ".png", ".jpg", ".jpeg", ".pdf", ".PNG", ".JPG", ".PDF"]
    for d in [""] + gpaths:
        for e in exts:
            p = root / d / (name + e)
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf"):
                return p
    stem = Path(name).name
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf") and (p.stem == Path(stem).stem or p.name == stem):
            return p
    return None


def parse_eprint(aid: str) -> tuple[list[dict], str]:
    d = EPRINT / aid
    d.mkdir(parents=True, exist_ok=True)
    pkg = d / "pkg"
    if not pkg.exists():
        st, data, _, ctype = get(f"https://arxiv.org/e-print/{aid}", limit=EPRINT_MAX)
        if st != 200:
            return [], f"e-print {st}"
        if len(data) > EPRINT_MAX:
            return [], "e-print 超过 80 MB"
        pkg.write_bytes(data)
    data = pkg.read_bytes()
    x = d / "x"
    if not x.exists():
        x.mkdir()
        if data[:4] == b"%PDF":
            return [], "e-print 只有 PDF"
        raw = data
        try:
            with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
                tf.extractall(x, filter="data")
        except tarfile.ReadError:
            try:
                raw = gzip.decompress(data)
            except OSError:
                return [], "e-print 格式不认识"
            try:
                with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
                    tf.extractall(x, filter="data")
            except tarfile.ReadError:
                (x / "main.tex").write_bytes(raw)
    mains = [p for p in x.rglob("*.tex") if "\\documentclass" in p.read_text(encoding="utf-8", errors="ignore")]
    if not mains:
        return [], "源码包里没有主 tex 文件"
    main = max(mains, key=lambda p: p.stat().st_size)
    root = main.parent
    s = expand_tex(root, main, set())
    gpaths = [g for grp in re.findall(r"\\graphicspath\{((?:\{[^}]*\})+)\}", s) for g in re.findall(r"\{([^}]*)\}", grp)]
    out = []
    n = 0
    for m in re.finditer(r"\\begin\{(figure\*?|wrapfigure)\}(.*?)\\end\{\1\}", s, re.S):
        body = m.group(2)
        n += 1
        ci = body.find("\\caption")
        caption = ""
        if ci >= 0:
            caption, _ = brace_arg(body, ci + len("\\caption"))
            caption = tex_to_text(caption)
        incs = re.findall(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}", body)
        found = [find_graphic(root, g, gpaths) for g in incs]
        if not found or None in found:
            continue  # 有子图找不到（EPS 等），拼出来会缺，不用
        panels = [{"img": p.relative_to(HERE).as_posix(), "w": 0, "h": 0, "row": 0} for p in found]
        best = max(found, key=lambda p: p.stat().st_size)
        out.append({"fig_no": f"Figure {n}", "caption": caption, "img": best.relative_to(HERE).as_posix(),
                    "w": 0, "h": 0, "n_panels": len(panels), "kind": "eprint", "panels": panels})
    for i, c in enumerate(out):
        c["idx"] = i
    return out, "" if out else "源码包里没找到能用的图（可能是 EPS 或 TikZ）"


# ---------------------------------------------------------------- 每篇论文

LOCK = threading.Lock()


def save_json(path: Path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def read_license(aid: str) -> str | None:
    st, data, _, _ = get(f"https://export.arxiv.org/abs/{aid}")
    if st != 200:
        return None
    m = re.search(rb'class="abs-license"><a href="([^"]+)"', data)
    if m:
        return m.group(1).decode()
    m = re.search(rb'href="(https?://(?:creativecommons\.org|arxiv\.org/licenses)/[^"]+)"', data)
    return m.group(1).decode() if m else None


def missing_figs(cs: list[dict]) -> bool:
    """网页版少于 2 张图，或图号有缺（转换时丢了图），返回 True。"""
    nums = {int(m.group(1)) for c in cs if (m := re.fullmatch(r"(?:Figure|Fig\.?)\s*(\d+)", c["fig_no"]))}
    return len(cs) < 2 or bool(nums) and max(nums) > len(nums)


PARSER_VERSION = 4


def do_paper(aid: str, cands: dict):
    rec = cands.get(aid) or {}
    if rec.get("status") == "ok" and rec.get("pv") != PARSER_VERSION and rec["source"] in ("html", "ar5iv"):
        html, final = cached_page(aid, rec["source"], rec["source_url"])
        rec["candidates"] = parse_html(html, final)
    if rec.get("status") == "ok" and rec.get("pv") != PARSER_VERSION and rec["source"] == "eprint":
        rec["candidates"], rec["note"] = parse_eprint(aid)
    rec["pv"] = PARSER_VERSION
    thin = rec.get("source") == "html" and not rec.get("ar5iv_checked") and missing_figs(rec["candidates"])
    if rec.get("status") == "ok" and rec.get("license_checked") and not thin:
        with LOCK:
            cands[aid] = rec
        return
    if not rec.get("license_checked"):
        rec["license"] = read_license(aid)
        rec["license_checked"] = True
    if rec.get("status") != "ok" or thin:
        # 网页版图少或图号有缺时（多是转换丢图）再看 ar5iv，取图多的一边
        best = ([], None, None)
        for tag, url in (("html", f"https://arxiv.org/html/{aid}"), ("ar5iv", f"https://ar5iv.labs.arxiv.org/html/{aid}")):
            html, final = cached_page(aid, tag, url)
            figs = parse_html(html, final) if html else []
            if len(figs) > len(best[0]):
                best = (figs, tag, final)
            if best[0] and not missing_figs(best[0]):
                break
        if rec.get("source") == "html" and best[1] == "ar5iv":
            rec["switched_from_html"] = True
        figs, src, page = best
        note = ""
        rec["ar5iv_checked"] = True
        if not figs:
            figs, note = parse_eprint(aid)
            if figs:
                src, page = "eprint", f"https://arxiv.org/abs/{aid}"
        rec.update({"source": src, "source_url": page, "candidates": figs, "note": note,
                    "status": "ok" if figs else "none"})
    with LOCK:
        cands[aid] = rec
        save_json(CAND_F, cands)
    print(f"{aid}: {rec['status']} {rec.get('source')} {len(rec['candidates'])} 图 {rec.get('note','')}", flush=True)


# ---------------------------------------------------------------- 选图

GOOD = ["architecture", "overview", "illustrat", "structure", "module", "block", "framework", "pipeline",
        "diagram", "schematic", "design", "proposed", "detail", "mechanism", "layer", "workflow", "flowchart",
        "computation", "operation", "unit", "attention"]
BAD = [r"visuali[sz]", r"curves?\b", r"\bplots?\b", r"heat ?maps?", r"t-?sne", r"grad-?cam", r"qualitative",
       r"\bsamples?\b", r"\bexamples?\b", r"accuracy", r"top-1", r"\bmap\b", r"\bAP\b", r"performance",
       r"\bresults?\b", r"trade-?off", r"latency", r"throughput", r"\bspeed", r"flops", r"\bloss\b",
       r"training", r"convergence", r"ablation", r"\bvs\.?\b", r"versus", r"distribution", r"histogram",
       r"statistic", r"benchmark", r"attention maps?\b", r"activation maps?", r"\bcorrelation",
       r"perplexity", r"psnr", r"miou", r"\bdataset", r"\bscores?\b", r"improvement", r"evaluation"]
STOP = set("a an the of for and with in on to via by from is are towards toward using based network networks "
           "learning efficient deep neural model models image images vision visual".split())


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def name_hit(name: str, cap: str) -> bool:
    if not name:
        return False
    if len(squash(name)) <= 3:
        return re.search(r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])", cap) is not None
    return squash(name) in squash(cap)


def score(c: dict, ex: dict) -> float:
    cap = c["caption"]
    low = cap.lower()
    s = 0.0
    names = {ex.get("name_en") or ""}
    names.add(re.sub(r"[-_]", "", ex.get("name_en") or ""))
    names.add(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", ex.get("name_en") or ""))
    if any(name_hit(n, cap) for n in names if n):
        s += 10
    s += 4 * min(3, sum(1 for g in GOOD if g in low))
    s -= 6 * sum(1 for b in BAD if re.search(b, cap, re.I))
    tw = {w for w in re.findall(r"[a-z]{4,}", (ex.get("title") or "").lower()) if w not in STOP}
    if len(tw & set(re.findall(r"[a-z]{4,}", low))) >= 2:
        s += 3
    m = re.search(r"(\d+)", c["fig_no"] or "")
    if m and int(m.group(1)) <= 3:
        s += 2
    s -= 0.4 * c["idx"]
    if c["kind"] == "inline-svg":
        s -= 1
    if c["n_panels"] > 4 and c["w"] and c["w"] < 160:
        s -= 4
    if not cap:
        s -= 3
    return s


def choose(ex: dict, rec: dict, ovr: dict):
    cs = rec.get("candidates") or []
    if ex["id"] in ovr:
        k = ovr[ex["id"]]
        if k is not None and cs[k]["kind"] in ("inline-svg", "mixed"):
            raise ValueError(f"{ex['id']}: 候选 {k} 是内嵌 SVG，取不下来")
        return None if k is None else cs[k]
    cs = [c for c in cs if c["kind"] not in ("inline-svg", "mixed")]
    if not cs:
        return None
    best = max(cs, key=lambda c: score(c, ex))
    return best if score(best, ex) >= 0 else None  # 负分多是曲线、样例、可视化，宁缺


# ---------------------------------------------------------------- 存图


def save_raster(im: Image.Image, out: Path):
    w = min(im.width, MAX_W)
    while True:
        cur = im if im.width == w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        for kw in ({"lossless": True, "method": 6}, {"quality": 90, "method": 6}, {"quality": 80, "method": 6}):
            buf = io.BytesIO()
            cur.save(buf, "WEBP", **kw)
            if buf.tell() <= TARGET_BYTES:
                out.write_bytes(buf.getvalue())
                return
        if w <= 700:
            out.write_bytes(buf.getvalue())
            return
        w = int(w * 0.8)


UNIT_PX = {"": 1.0, "px": 1.0, "pt": 96 / 72, "pc": 16.0, "in": 96.0, "cm": 96 / 2.54, "mm": 96 / 25.4}


def svg_size(svg: str) -> tuple[float, float]:
    """读根元素的 width/height（带单位），没有时用 viewBox。先算尺寸再渲染，免得超大画布按原尺寸渲染一遍。"""
    head = svg[:svg.find(">", svg.find("<svg")) + 1]
    dims = []
    for k in ("width", "height"):
        m = re.search(rf'\s{k}="([\d.]+)\s*(px|pt|pc|in|cm|mm|)"', head)
        dims.append(float(m.group(1)) * UNIT_PX[m.group(2)] if m else None)
    if None in dims:
        vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', head)
        dims = [float(vb.group(1)), float(vb.group(2))]
    return dims[0], dims[1]


def render_svg(data: bytes, width: int | None = None) -> bytes:
    """SVG 转 PNG，白底。给了 width 就渲染到这个宽度，否则宽 1200 px、高 1600 px 以内，最多放大 3 倍。"""
    svg = data.decode("utf-8", errors="ignore")
    w0, h0 = svg_size(svg)
    zoom = width / w0 if width else min(MAX_W / w0, 1600 / h0, 3.0)
    return bytes(resvg_py.svg_to_bytes(svg_string=svg, dpi=96.0, zoom=zoom, background="#ffffff"))


def load_panel(c: dict, p: dict, width: int | None) -> Image.Image:
    """取一个子图，返回白底 RGB 图。width 给定时 SVG 按这个宽度渲染。"""
    src = p["img"]
    if c["kind"] == "eprint":
        f = HERE / src
        if f.suffix.lower() == ".pdf":
            if not PDFTOPPM:
                raise RuntimeError("找不到 pdftoppm")
            out = f.with_name(f.name + ".render")
            subprocess.run([PDFTOPPM, "-png", "-r", "200", "-f", "1", "-l", "1", "-singlefile", str(f), str(out)], check=True)
            f = Path(str(out) + ".png")
        return flatten(Image.open(f))
    st, data, _, ctype = get(src)
    if st != 200:
        raise RuntimeError(f"图片 {st}: {src}")
    if src.lower().endswith(".svg") or "svg" in ctype:
        data = render_svg(data, width)
    return flatten(Image.open(io.BytesIO(data)))


def flatten(im: Image.Image) -> Image.Image:
    im.seek(0)
    if im.mode in ("RGBA", "LA", "P", "PA") or "transparency" in im.info:
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[3])
        return bg
    return im.convert("RGB")


def trim_white(im: Image.Image, pad: int = 6) -> Image.Image:
    """裁掉接近纯白的外边框，留 pad 像素。"""
    gray = im.convert("L").point(lambda v: 255 if v < 245 else 0)
    box = gray.getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


COMPOSE_VERSION = "c2"  # 拼图规则改了就换这个值，多子图的图会重新生成


def compose(c: dict) -> Image.Image:
    """多子图按论文网页里的行和显示尺寸拼成整张图，单子图原样返回。"""
    panels = c["panels"]
    if len(panels) == 1:
        return load_panel(c, panels[0], None)
    rows: dict[int, list] = {}
    for p in panels:
        rows.setdefault(p["row"], []).append(p)
    gap = 12
    if all(p["w"] and p["h"] for p in panels):
        row_w = max(sum(p["w"] for p in r) + gap * (len(r) - 1) for r in rows.values())
        s = min(MAX_W / row_w, 3.0)
        size = {id(p): (max(1, round(p["w"] * s)), max(1, round(p["h"] * s))) for p in panels}
        gap = round(gap * s)
    else:  # 源码包：没有显示尺寸，按原图像素，同一行等高
        size = {}
    ims = {}
    for p in panels:
        im = load_panel(c, p, size[id(p)][0] if size else None)
        ims[id(p)] = im
    if size:  # 去掉子图四周的白边，按原比例缩小目标尺寸（只裁空白，不裁内容）
        for p in panels:
            im = ims[id(p)]
            k = size[id(p)][0] / im.width
            ims[id(p)] = im = trim_white(im)
            size[id(p)] = (max(1, round(im.width * k)), max(1, round(im.height * k)))
    else:
        for p in panels:
            ims[id(p)] = trim_white(ims[id(p)])
        for r in rows.values():
            hgt = min(ims[id(p)].height for p in r)
            for p in r:
                im = ims[id(p)]
                size[id(p)] = (max(1, round(im.width * hgt / im.height)), hgt)
    groups = [rows[k] for k in sorted(rows)]
    stacked_h = sum(max(size[id(p)][1] for p in r) for r in groups)
    stacked_w = max(sum(size[id(p)][0] for p in r) for r in groups)
    if len(groups) > 1 and all(len(r) == 1 for r in groups) and stacked_h > 1.5 * stacked_w:
        groups = [[r[0] for r in groups]]  # 每行只有一张、竖着又太长时，并成一行（网页版的换行多是排版造成的）
    lines = []
    for r in groups:
        lines.append((r, sum(size[id(p)][0] for p in r) + gap * (len(r) - 1), max(size[id(p)][1] for p in r)))
    W = max(w for _, w, _ in lines)
    H = sum(h for _, _, h in lines) + gap * (len(lines) - 1)
    canvas = Image.new("RGB", (W, H), "white")
    y = 0
    for r, w, h in lines:
        x = (W - w) // 2
        for p in r:
            pw, ph = size[id(p)]
            canvas.paste(ims[id(p)].resize((pw, ph), Image.LANCZOS), (x, y))
            x += pw + gap
        y += h + gap
    return canvas


def fetch_image(ex: dict, c: dict) -> Path:
    """取回整张图（多子图拼合）并保存，返回文件路径。"""
    if c["kind"] in ("inline-svg", "mixed"):
        raise RuntimeError("含内嵌 SVG 的图取不全，不下载")
    out = FIG_DIR / f"{ex['id']}.webp"
    save_raster(compose(c), out)
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    for p in (PAGES, EPRINT, FIG_DIR):
        p.mkdir(parents=True, exist_ok=True)
    exs = [e for e in json.loads((HERE / "site/data/museum.json").read_text(encoding="utf-8"))["exhibits"] if e.get("arxiv")]
    if a.only:
        keep = set(a.only.split(","))
        exs = [e for e in exs if e["arxiv"] in keep]
    cands = json.loads(CAND_F.read_text(encoding="utf-8")) if CAND_F.exists() else {}
    aids = sorted({e["arxiv"] for e in exs})
    errors: dict[str, str] = {}

    def guarded(key, fn, *args):
        """单篇论文或单张图出错时记下来继续跑，结束时退出码非零。重跑会重试。"""
        try:
            fn(*args)
        except Exception as e:  # noqa: BLE001 记进 download_errors.json，最后非零退出
            errors[key] = f"{type(e).__name__}: {e}"
            print(f"{key}: 出错 {errors[key]}", flush=True)

    with ThreadPoolExecutor(a.workers) as pool:
        for f in [pool.submit(guarded, aid, do_paper, aid, cands) for aid in aids]:
            f.result()
    save_json(CAND_F, cands)

    ovr = json.loads(OVR_F.read_text(encoding="utf-8")) if OVR_F.exists() else {}
    dl = json.loads(DL_F.read_text(encoding="utf-8")) if DL_F.exists() else {}
    figs = json.loads(FIG_F.read_text(encoding="utf-8")) if FIG_F.exists() else {}

    def one(ex):
        rec = cands[ex["arxiv"]]
        c = choose(ex, rec, ovr)
        eid = ex["id"]
        if c is None:
            old = dl.get(eid)
            with LOCK:
                if old:
                    (HERE / old["file"]).unlink(missing_ok=True)
                    dl.pop(eid, None)
                figs.pop(eid, None)
            return
        old = dl.get(eid)
        key = "|".join(p["img"] for p in c["panels"])
        if len(c["panels"]) > 1:
            key = COMPOSE_VERSION + "|" + key
        if old and old.get("key") == key and (HERE / old["file"]).exists():
            path = old["file"]
        else:
            if old:
                (HERE / old["file"]).unlink(missing_ok=True)
            path = fetch_image(ex, c).relative_to(HERE).as_posix()
        entry = {"file": path.removeprefix("site/"), "fig_no": c["fig_no"], "caption": c["caption"],
                 "source_url": rec["source_url"], "license": rec.get("license")}
        with LOCK:
            dl[eid] = {"key": key, "file": path, "idx": c["idx"], "n_panels": c["n_panels"]}
            figs[eid] = entry
            save_json(DL_F, dl)
            save_json(FIG_F, figs)
        print(f"{eid}: {c['fig_no']} -> {path}", flush=True)

    if not a.no_download:
        with ThreadPoolExecutor(a.workers) as pool:
            for f in [pool.submit(guarded, e["id"], one, e) for e in exs if e["arxiv"] in cands]:
                f.result()
        if not a.only:  # 展品被改名或移出馆藏时，删掉它的旧图和记录
            live = {e["id"] for e in exs}
            for eid in [k for k in dl if k not in live]:
                (HERE / dl.pop(eid)["file"]).unlink(missing_ok=True)
                figs.pop(eid, None)
        with LOCK:
            save_json(DL_F, dl)
            save_json(FIG_F, dict(sorted(figs.items())))
    save_json(CACHE / "download_errors.json", errors)
    print(f"完成：{len(figs)} 件有图，{len(errors)} 处出错", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
