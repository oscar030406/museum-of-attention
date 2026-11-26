"""注意力博物馆的数据生成脚本。

读库里的 INDEX.md、各模块 README.md、模块目录里的 .py 文件头，
以及 工具与模板/模块收集/ 下的队列文件，写出 site/data/museum.json。
只读这些来源，不改它们。字段取不到就记为缺失，不补写。

另外合并 curation/ 下的馆长手写层：texts.part*.json（简介和英文文案）、figures.json（论文配图）、
story.json（导览稿）、paper_citations.json（OpenAlex 引用）和 paper_dates.json（arXiv 首次提交日）。
这些文件缺失时照常生成，只是少了对应内容。

用法：python build_data.py            本机自用，带全部论文配图
      python build_data.py --public   上线用，只带 Creative Commons 许可的配图
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from fetch_paper_metadata import identifiers

HERE = Path(__file__).resolve().parent
LIB = HERE.parent.parent                      # 收藏库的根目录，本项目在它下面两层
COLLECT = LIB / "工具与模板" / "模块收集"
OUT_DIR = HERE / "site" / "data"

QUEUE = COLLECT / "队列.md"
REPRO_QUEUE = COLLECT / "队列-论文复现.md"
VERIFY_LOG = COLLECT / "验证记录.md"
EXTEND_LOG = COLLECT / "扩队列记录.md"
INDEX = LIB / "INDEX.md"

ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf|html)/|arXiv[:：\s]*)(\d{4}\.\d{4,5})", re.I)
DOI_RE = re.compile(r"(?:doi\.org/|DOI[:：\s]+)(10\.\d{4,9}/[^\s)\]，。|`]+)", re.I)
GH_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")
YEAR_RE = re.compile(r"(?<!\d)(19[89]\d|20[0-3]\d)(?!\d)")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")

SOURCE_TYPES = {
    "author": "作者原版",
    "port": "官方移植",
    "repro": "照论文复现",
    "third": "第三方整理",
    "unknown": "来源未标明",
}

# 方向 a–k 的英文名，只用于界面显示；中文名从 扩队列记录.md 解析。
DIRECTION_EN = {
    "a": "Early attention", "b": "LLM attention 2022–2026", "c": "Multimodal & vision-language",
    "d": "Generative models", "e": "Video & time series", "f": "3D & point clouds", "g": "Graphs",
    "h": "Speech & audio", "i": "Detection, segmentation & dense prediction",
    "j": "Medical, remote sensing & low-level vision",
    "k": "Recommendation, tabular, RL & scientific computing",
}
FIELD_EN = {
    "计算机视觉": "Computer Vision", "深度学习基础": "Deep Learning Foundations",
    "自然语言处理": "Natural Language Processing", "语音与音频": "Speech & Audio",
    "多模态学习": "Multimodal Learning", "时间序列与时空数据": "Time Series & Spatio-temporal",
    "图学习": "Graph Learning", "视觉骨干与通用模块": "Backbones & General Modules",
    "图像分类与识别": "Classification & Recognition", "目标检测": "Object Detection",
    "图像分割": "Segmentation", "图像复原与增强": "Restoration & Enhancement",
    "图像生成与编辑": "Generation & Editing", "视频与动作理解": "Video & Action",
    "三维视觉与自动驾驶": "3D Vision & Driving",
}

# ---------------------------------------------------------------- 英文模式的对照表
# 取值有限的中文字段逐个对照。表里没有的取值，英文模式不显示，build 时打印出来以便补表。
CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")
DOMAIN_EN = {
    "通用": "General", "机器翻译": "Machine translation", "问答": "Question answering",
    "图像描述": "Image captioning", "自然语言推断": "Natural language inference", "文档问答": "Document QA",
    "阅读理解": "Reading comprehension", "医学": "Medical", "视觉问答": "Visual question answering",
    "行人重识别": "Person re-identification", "语言建模": "Language modeling",
    "视觉语言预训练": "Vision-language pretraining", "音乐生成": "Music generation", "超分辨率": "Super-resolution",
    "细粒度图像识别": "Fine-grained recognition", "语音识别": "Speech recognition", "长文本": "Long text",
    "文本理解": "Text understanding", "交通预测": "Traffic forecasting", "异构图": "Heterogeneous graphs",
    "分子性质预测": "Molecular property prediction", "点云": "Point clouds", "动作识别": "Action recognition",
    "视频理解": "Video understanding", "长时序预测": "Long-horizon forecasting",
    "流式语音识别": "Streaming speech recognition", "语言引导目标检测": "Language-guided detection",
    "放射学报告生成": "Radiology report generation", "多步时序预测": "Multi-step forecasting",
    "图文理解与生成": "Image-text understanding and generation",
    "语音识别与理解": "Speech recognition and understanding", "时序预测": "Time-series forecasting",
    "图学习": "Graph learning", "长文本处理": "Long-text processing",
    "视觉语言序列建模": "Vision-language sequence modeling", "语言模型": "Language models", "红外": "Infrared imaging",
    "工业缺陷": "Industrial defect detection", "遥感": "Remote sensing", "大语言模型推理": "LLM inference",
    "图文指令理解": "Visual instruction following", "长序列建模": "Long-sequence modeling",
    "图像、视频与文本": "Images, video and text", "图文理解与视觉定位": "Image-text understanding and grounding",
    "事件相机": "Event cameras", "节点分类": "Node classification", "显微成像": "Microscopy",
    "图形界面视觉理解": "GUI understanding", "视频摘要": "Video summarization", "动作分割": "Action segmentation",
    "开放词汇目标检测": "Open-vocabulary detection", "多模态视觉投影": "Multimodal visual projection",
    "图文定位与理解": "Image-text grounding and understanding",
    "语言模型参数高效微调": "Parameter-efficient fine-tuning", "大语言模型微调": "LLM fine-tuning",
    "扩散生成": "Diffusion generation", "时间序列预测": "Time-series forecasting", "视频生成": "Video generation",
    "视觉语言": "Vision-language", "图像生成": "Image generation", "视频目标跟踪": "Video object tracking",
    "多视图三维重建": "Multi-view 3D reconstruction", "密集预测": "Dense prediction", "立体匹配": "Stereo matching",
    "视频目标分割": "Video object segmentation", "小型语言模型": "Small language models", "图像编辑": "Image editing",
    "长上下文语言模型": "Long-context language models", "多图与视频语言建模": "Multi-image and video language modeling",
    "图像压缩": "Image compression", "语义分割": "Semantic segmentation", "序列建模": "Sequence modeling",
    "多视角三维重建": "Multi-view 3D reconstruction", "长上下文推理": "Long-context inference",
    "多视图几何重建": "Multi-view geometry reconstruction", "多模态推理加速": "Faster multimodal inference",
    "高分辨率图文理解": "High-resolution image-text understanding",
}
MTYPE_EN = {
    "注意力": "Attention", "卷积": "Convolution", "动态路由": "Dynamic routing", "时序建模": "Temporal modeling",
    "上下采样": "Up- and downsampling", "频域与小波": "Frequency domain and wavelets", "位置编码": "Positional encoding",
    "状态空间模型": "State-space model", "门控循环网络": "Gated recurrent network", "保留机制": "Retention",
    "循环序列混合": "Recurrent sequence mixing", "注意力与状态空间模型": "Attention and state-space model",
    "KV 缓存压缩": "KV-cache compression", "适配器": "Adapter", "循环与记忆": "Recurrence and memory",
    "注意力与 KV 缓存": "Attention and KV cache", "混合序列层": "Hybrid sequence layer",
    "注意力与状态空间": "Attention and state space", "记忆、注意力": "Memory and attention",
}
GUO_EN = {"通道": "channel", "空间": "spatial", "时间": "temporal", "分支": "branch"}
YEAR_SOURCE_EN = {"队列": "the collection queue", "README": "the README", "INDEX": "the library index",
                  "arXiv 编号": "the arXiv ID", "代码文件名": "the code file name"}
VER_SOURCE_EN = {"README": "the README", "验证记录.md": "the verification log", "队列-论文复现.md": "the rewrite queue"}
VENUE_EN = {"技术报告": "Technical report", "arXiv 技术报告": "arXiv technical report", "作者项目": "Author project", "ECCV Workshops（论文集": "ECCV Workshops"}
LICENSE_EN = {"未见明确许可证": "No clear license found", "通义千问协议": "Tongyi Qianwen License",
              "EPFL 非商业许可": "EPFL non-commercial license"}
MECH_SOURCE_CURATOR = "馆长依据摘要撰写"
unmapped: dict[str, set] = defaultdict(set)     # 对照表里缺的取值，build 结束时打印


def ascii_only(s: str | None) -> str | None:
    """英文模式能直接显示的文字：去掉首尾空白后不含中日韩字符。"""
    s = (s or "").strip()
    return s if s and not CJK.search(s) else None


EN_TERMS: dict[str, dict] = {}


def table_en(table: dict, kind: str, v: str | None) -> str | None:
    if not EN_TERMS and (HERE / "curation" / "en_terms.json").is_file():     # 馆藏扩充带进来的取值，译文放在馆长层
        EN_TERMS.update(json.loads((HERE / "curation" / "en_terms.json").read_text(encoding="utf-8")))
    table = {**EN_TERMS.get(kind, {}), **table}
    if not v:
        return None
    if v in table or ascii_only(v):
        return table.get(v, v)
    unmapped[kind].add(v)
    return None


def guo_en(v: str | None) -> str | None:
    if not v:
        return None
    parts = re.split(r"[与和、]", v)
    if all(p in GUO_EN for p in parts):
        return " and ".join(GUO_EN[p] for p in parts).capitalize()
    unmapped["guo"].add(v)
    return None


def license_en(key: str | None, raw: str | None) -> str | None:
    """许可证英文名：能归成短名的用短名；「其他」取原文「·」「。」之前的部分再对照。"""
    if not key:
        return None
    if key != "其他":
        return LICENSE_EN.get(key, key)
    head = re.split(r"\s*[·。]", raw or "", maxsplit=1)[0].strip()
    return table_en(LICENSE_EN, "license", head)


def authors_en(s: str | None) -> str | None:
    """作者名：「、」换成逗号，「和」换成 and，去掉带中文的括注和说明句。剩下仍有中文就不显示。"""
    if not s:
        return None
    s = re.sub(r"（[^）]*）", "", s)
    s = s.replace("、", ", ").replace(" 和 ", " and ")
    parts = [p.strip() for p in re.split(r"[。，]", s)]
    out = ". ".join(p for p in parts if p and not CJK.search(p))
    return out or None


def title_en(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\s*-\s*副本$", "", s).replace("（", " (").replace("）", ")")
    return ascii_only(s)


# ---------------------------------------------------------------- 通用小工具

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def md_rows(text: str, header_startswith: str) -> list[list[str]]:
    """取以 header_startswith 开头的那张 Markdown 表的数据行，按 | 切成单元格。"""
    rows, on = [], False
    for line in text.splitlines():
        if line.startswith(header_startswith):
            on = True
            continue
        if on:
            if not line.startswith("|"):
                if rows:
                    break
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
    return rows


def strip_md(s: str) -> str:
    s = LINK_RE.sub(r"\1", s)
    return s.replace("`", "").replace("**", "").strip()


def first_link(s: str) -> str | None:
    m = LINK_RE.search(s)
    return m.group(2) if m else None


def norm_title(t: str | None) -> str | None:
    if not t:
        return None
    k = re.sub(r"[^a-z0-9]", "", t.lower())
    return k[:40] if len(k) >= 12 else None


def base_name(en: str) -> str:
    b = re.sub(r"-(官方原版|论文复现)$", "", en.strip())
    b = re.sub(r"-[A-Z][A-Za-z]*\d{4}$", "", b)
    b = re.sub(r"-(官方原版|论文复现)$", "", b)
    return b.strip()


def year_from_arxiv(aid: str | None) -> int | None:
    if not aid:
        return None
    yy = int(aid[:2])
    return 2000 + yy if 7 <= yy <= 40 else None


def parse_venue(s: str | None) -> tuple[int | None, str | None]:
    """把「ICCVW 2019」「2018 CVPR」「arXiv 2206.09959」「未标注」拆成 (年份, 出处)。"""
    if not s:
        return None, None
    s = strip_md(s)
    if not s or s in ("未标注", "—", "-"):
        return None, None
    m = re.fullmatch(r"arXiv\s*(\d{4}\.\d{4,5})", s, re.I)
    if m:
        return year_from_arxiv(m.group(1)), "arXiv"
    y = YEAR_RE.search(s)
    year = int(y.group(1)) if y else None
    venue = YEAR_RE.sub("", s).strip(" ，,()（）") or None
    if venue and re.search(r"\s·\s", venue):      # 「CVPR 2022 · arXiv 2203.11192 · 会议论文」只留会议名
        venue = re.split(r"\s+·\s+", venue)[0].strip() or None
    return year, venue


# ---------------------------------------------------------------- 读 INDEX

def load_index() -> list[dict]:
    text = read(INDEX)
    sec = text.split("## 模块总表", 1)[1].split("\n## ", 1)[0]
    rows = md_rows(sec, "| 中文名 |")
    out = []
    for c in rows:
        if len(c) < 9:
            continue
        zh, en, venue, mtype, domain, pdf, code, path, note = c[:9]
        path = path.strip("`").strip()
        title = None
        m = re.search(r"论文：([^；|]+)", note)
        if m:
            title = m.group(1).strip()
            if "无论文" in title:
                title = None
        src = re.search(r"来源：([^；|（(]+)", note)
        out.append(dict(name_zh=zh, name_en=en, venue_raw=venue, module_type=mtype,
                        domain=domain, has_pdf=pdf, has_code=code, path=path,
                        note=note, title=title, index_source=src.group(1).strip() if src else None))
    return out


# ---------------------------------------------------------------- 读队列

GUO_TAG = re.compile(r"^\s*((?:通道|空间|时间|分支)(?:[与和、](?:通道|空间|时间|分支))*)。")
LICENSES = [("CC-BY-NC-SA-4.0", r"CC[- ]BY[- ]NC[- ]SA"), ("CC-BY-NC-4.0", r"CC[- ]BY[- ]NC"), ("FAIR-NC", r"FAIR Noncommercial"), ("NVIDIA-NC", r"NVIDIA Source Code License|Nvidia Source Code License"),
            ("Apache-2.0", r"Apache"), ("BSD-3-Clause-Clear", r"BSD-3-Clause-Clear"), ("BSD-3-Clause", r"BSD[- ]3"),
            ("BSD-2-Clause", r"BSD-2"), ("BSD", r"\bBSD\b"), ("GPL-3.0", r"GPL-3|GPLv3"), ("GPL-2.0", r"GPL-2|GPLv2"),
            ("LGPL", r"LGPL"), ("MIT", r"\bMIT\b"), ("CC-BY-4.0", r"CC[- ]BY[- ]4"), ("MPL-2.0", r"MPL"),
            ("未见明确许可证", r"未见|未声明|未登记|无许可|没有许可|未列")]


def license_key(raw: str | None) -> str | None:
    """把许可证原文归成一个短名，原文另存。"""
    if not raw:
        return None
    hits = [(m.start(), i, key) for i, (key, pat) in enumerate(LICENSES) if (m := re.search(pat, raw))]
    return min(hits)[2] if hits else "其他"     # 原文里最先出现的许可证；同一位置取规则表里靠前的


def guo_of(note: str) -> str | None:
    m = GUO_TAG.match(strip_md(note))
    return m.group(1) if m else None


def clean_mechanism(note: str) -> str | None:
    """从队列备注里去掉收录目录、许可和仓库这类管理信息，留下描述机制的句子。"""
    s = strip_md(note)
    s = re.sub(r"(收录|已收)目录\s*\S+?。", "", s)
    s = GUO_TAG.sub("", s)
    sents = [x.strip() for x in re.split(r"(?<=。)", s) if x.strip()]
    admin = re.compile(r"^(补作者原版|作者原版|补官方|收录|跳过|论文复现|未见|仓库|根目录|许可|代码沿用|固定提交|另见|见 |综述)|许可|LICENSE|根目录|提交|未列|404|403|收录目录|`论文复现|OpenAlex")
    keep = [x for x in sents if not admin.search(x)]
    text = "".join(keep[:2]).strip()
    return text or None


def load_extend_log() -> dict:
    """解析 扩队列记录.md：方向 a–k 的名字、每段的序号范围和各方向条数、待扫方向。"""
    text = read(EXTEND_LOG)
    directions: dict[str, dict] = {}
    main_ranges: list[tuple[int, int, list[tuple[str, int]]]] = []
    repro_ranges: list[tuple[int, int, list[tuple[str, int]]]] = []
    pending: list[str] = []
    for sec in re.split(r"\n(?=## )", text):
        rng = re.search(r"追加\s*\d+\s*条待收，序号\s*(\d+)[–-](\d+)", sec)
        rrng = re.search(r"论文复现队列追加\s*\d+\s*条候选，序号\s*(\d+)[–-](\d+)", sec)
        main_counts, repro_counts = [], []
        # 两种写法：列表项「- **a. 名字**。追加 N 条…」和表格行「| a. 名字 | 待收 | 复现建议（可省）| 来源 |」
        items = [(l, n, rest, re.search(r"追加\s*(\d+)\s*条", rest), re.search(r"(\d+)\s*条候选", rest))
                 for l, n, rest in re.findall(r"^- \*\*([a-k])\. ([^*]+?)\*\*。(.*)$", sec, re.M)]
        items += [(l, n, rest, re.match(r"(\d+)", c), None)
                  for l, n, c, rest in re.findall(r"^\| ([a-k])\. ([^|]+?) \| *(\d+) *\|(?: *\d+ *\|)?(.*)$", sec, re.M)]
        for letter, name, rest, mm, rr in items:
            d = directions.setdefault(letter, {"zh": name.strip("。 ")})
            d["scanned"] = True
            d.setdefault("sources", [])
            for l, u in LINK_RE.findall(rest):
                if all(x["url"] != u for x in d["sources"]):
                    d["sources"].append({"label": l, "url": u})
            main_counts.append((letter, int(mm.group(1)) if mm else 0))
            repro_counts.append((letter, int(rr.group(1)) if rr else 0))
        if rng:
            main_ranges.append((*map(int, rng.groups()), main_counts))
        if rrng:
            repro_ranges.append((*map(int, rrng.groups()), repro_counts))
        pm = re.search(r"### 待扫方向\s*\n+(.+)", sec)
        if pm:
            for letter, name in re.findall(r"([a-k])\. ([^，。]+)", pm.group(1)):
                directions.setdefault(letter, {"zh": name.strip()})
                directions[letter].setdefault("scanned", False)
                pending.append(letter)

    def assign(ranges):
        m = {}
        for a, b, counts in ranges:
            if sum(n for _, n in counts) != b - a + 1:
                print(f"注意：扩队列记录里序号 {a}–{b} 的各方向条数加起来是 {sum(n for _, n in counts)}，对不上，这一轮没有分配方向")
                continue        # 条数对不上就不分配，宁缺不错
            i = a
            for letter, n in counts:
                for _ in range(n):
                    m[i] = letter
                    i += 1
        return m

    for k, v in directions.items():
        v["en"] = DIRECTION_EN.get(k)
    return dict(directions=directions, main_map=assign(main_ranges),
                repro_map=assign(repro_ranges),
                pending=[k for k in sorted(directions) if not directions[k].get("scanned")])


def load_queue(ext: dict) -> list[dict]:
    rows = md_rows(read(QUEUE), "| 序号 |")
    out = []
    for c in rows:
        if len(c) < 12 or not c[0].isdigit():
            continue
        no = int(c[0])
        note = c[11]
        path = None
        m = re.search(r"`(论文复现/[^`]*（[^`]*）)/?`", note)
        if m:
            path = m.group(1).strip()
        year, venue = parse_venue(c[5])
        ident = c[6]
        aid = ARXIV_RE.search(ident)
        doi = DOI_RE.search(ident)
        repo = GH_RE.search(c[7])
        out.append(dict(
            queue="main", no=no, status=c[1], segment=c[2], name_en=strip_md(c[3]),
            title=strip_md(c[4]), year=year, venue=venue,
            arxiv=aid.group(1) if aid else None, doi=doi.group(1).rstrip(".") if doi else None,
            paper_url=first_link(ident), repo=repo.group(1) if repo else None,
            repo_url=first_link(c[7]), source_file_url=first_link(c[8]),
            license=strip_md(c[9]) or None, hall_dir=c[10].strip("`").strip(),
            note=strip_md(note), mechanism=clean_mechanism(note), path=path,
            direction=ext["main_map"].get(no),
        ))
    return out


def load_repro_queue(ext: dict) -> list[dict]:
    rows = md_rows(read(REPRO_QUEUE), "| 序号 |")
    out = []
    for c in rows:
        if len(c) < 6 or not c[0].isdigit():
            continue
        no = int(c[0])
        paper = c[3]
        parts = [p.strip() for p in strip_md(paper).split("，")]
        title = parts[0] if parts else None
        year = venue = None
        for p in parts[1:]:
            y, v = parse_venue(p)
            if y and not year:
                year, venue = y, v
        aid = ARXIV_RE.search(paper)
        doi = DOI_RE.search(paper)
        note = c[5]
        path = None
        m = re.search(r"`(论文复现/[^`]*（[^`]*）)/?`", note)
        if m:
            path = m.group(1).strip()
        out.append(dict(
            queue="repro", no=no, status=c[1], segment="复现", name_en=strip_md(c[2]),
            title=title, year=year, venue=venue,
            arxiv=aid.group(1) if aid else None, doi=doi.group(1).rstrip(".") if doi else None,
            paper_url=first_link(paper), repo=None, repo_url=None, source_file_url=None,
            license=None, hall_dir=c[4].strip("`").strip(), note=strip_md(note),
            mechanism=None if path else clean_mechanism(note), path=path,
            verify=strip_md(c[6]) if len(c) > 6 else None,
            direction=ext["repro_map"].get(no),
        ))
    return out


def load_verify_log() -> dict[str, str]:
    """验证记录.md 里每个模块的「核对结论」列。键是表里的模块名。"""
    out = {}
    for sec in re.split(r"\n(?=## )", read(VERIFY_LOG)):
        for c in md_rows(sec, "| 模块 |"):
            if len(c) >= 2:
                out[c[0].strip()] = strip_md(c[1])
    return out


def load_no_code_list() -> list[dict]:
    text = read(QUEUE)
    if "## 没有官方代码" not in text:
        return []
    sec = text.split("## 没有官方代码", 1)[1].split("\n## ", 1)[0]
    out = []
    for name, rest in re.findall(r"^- \*\*([^*]+)\*\*。(.*)$", sec, re.M):
        out.append(dict(name=name, reason=strip_md(re.sub(r"\s*\[[^\]]*\]\([^)]*\)", "", rest)),
                        url=first_link(rest)))
    return out


# ---------------------------------------------------------------- 读模块目录

def kv_field(text: str, keys: list[str]) -> str | None:
    """取「- 键｜值」「- 键：值」「- 键 值」「- 键为值」「| 键 | 值 |」「**键**：值」和正文「键为值。」里的值。"""
    for k in keys:
        pats = (rf"^- {k}[｜：:]\s*(.+)$", rf"^\| *{k} *\| *(.+?) *\|\s*$", rf"^\*\*{k}\*\*[｜：:]\s*(.+)$",
                rf"^- {k}(?:为|\s+)(?!PDF|编号|\d)(.+)$", rf"(?:^|。)\s*{k}为\s*([^。\n]+)")
        for pat in pats:
            m = re.search(pat, text, re.M)
            if m:
                return m.group(1).strip()
    return None


REPO_URL_RE = re.compile(r"https?://(?:github\.com|huggingface\.co|gitlab\.com|gitee\.com)/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def repo_of(line: str | None) -> tuple[str | None, str | None]:
    """从一行文字里取仓库：返回 (显示名, 地址)。GitHub 显示 owner/name，其他站点带上站名。"""
    if not line:
        return None, None
    m = REPO_URL_RE.search(line)
    if not m:
        return None, None
    url = m.group(0).rstrip(".")
    host, owner, name = url.split("/")[2:5]
    label = f"{owner}/{name}" if host == "github.com" else f"{host.split('.')[0]}: {owner}/{name}"
    return label, f"https://{host}/{owner}/{name}"


VERIFY_HEADS = r"(数值验证|数值对照|等价性|数值核对|数值等价性|CPU 示例与对照|CPU 示例与数值对照|CPU 验证|CPU 自测)"


def section(text: str, head_re: str) -> str | None:
    m = re.search(rf"^## {head_re}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(2).strip() if m else None


VERIFY_KEY = r"最大(绝对)?差|误差|一致|相同|通过|对照|阈值|核对"


def summarize_verification(text: str) -> str | None:
    """取 README 核对小节的前两句。只有「CPU 示例」一节时，只认带核对关键词的句子。"""
    sec = section(text, VERIFY_HEADS)
    strict = sec is None
    if strict:
        sec = section(text, r"(CPU 示例)")
    if not sec:
        return None
    body = re.sub(r"```.*?```", "", sec, flags=re.S)
    lines = [l.strip("- ").strip() for l in body.splitlines()]
    lines = [l for l in lines if l and not l.startswith("|") and not re.fullmatch(r"`[^`]*`", l)]  # 去掉整行的运行命令
    body = strip_md(" ".join(lines))
    sents = [x for x in re.split(r"(?<=。)", body) if x.strip()]
    key = [x for x in sents if re.search(VERIFY_KEY, x)]
    if strict and not key:
        return None
    res = [x for x in key if re.search(r"差(?:值)?(?:均|都)?(?:为|是)", x) and not re.search(r"阈值为", x.split("差")[0][-6:])]
    pick = [x for x in key if x in (key[:1] + res[:1])] if res else (key or sents)[:2]
    s = "".join(pick).strip()
    return s[:220] + ("…" if len(s) > 220 else "") if s else None


def read_module_dir(path: str) -> dict:
    d = LIB / path
    info: dict = {"exists": d.is_dir()}
    if not d.is_dir():
        return info
    readme = d / "README.md"
    text = read(readme) if readme.exists() else ""
    info["readme"] = readme.exists()
    pys = sorted(d.glob("*.py"))
    head = read(pys[0])[:3000] if pys else ""
    info["py_files"] = [p.name for p in pys]
    blob = text + "\n" + head

    title = kv_field(text, ["论文", "论文原题", "论文题目", "题目"])
    if title:
        title = strip_md(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)).strip(" 。*")
    if not title:
        m = re.search(r"#\s*论文题目[：:]\s*(.+)", head)
        if m:
            title = m.group(1).strip()
    if not title and text.startswith("# ") and re.match(r"# [A-Za-z]", text):
        title = text.splitlines()[0][2:].strip()
    info["title"] = title or None

    authors = kv_field(text, ["作者"])
    info["authors"] = strip_md(authors).rstrip("。") if authors else None
    venue = kv_field(text, ["出处"])
    if venue:
        venue = strip_md(venue).split("。")[0]
    info["venue_raw"] = venue
    aid = ARXIV_RE.search(blob)
    info["arxiv"] = aid.group(1) if aid else None
    doi = DOI_RE.search(blob)
    info["doi"] = doi.group(1).rstrip(".") if doi else None

    repo_line = kv_field(text, ["官方仓库", "原始仓库", "源码发行仓库", "官方源码", "官方实现", "仓库"])
    if repo_line and not REPO_URL_RE.search(repo_line):
        m = re.search(r"`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)`", repo_line)    # 「仓库为 `owner/name`」
        repo_line = f"https://github.com/{m.group(1)}" if m else repo_line
    if not repo_line:
        m = re.search(r"#\s*官方github[：:]\s*(\S+)", head, re.I)
        repo_line = m.group(1) if m else None
    info["repo"], info["repo_url"] = repo_of(repo_line)
    m = re.search(r"#\s*论文链接[：:]\s*(?:\n#\s*)?(https?://\S+)", head)
    info["paper_url"] = m.group(1) if m else None
    cm = COMMIT_RE.search(text)
    info["commit"] = cm.group(0) if cm else None
    src = kv_field(text, ["模块源文件", "源文件"])
    info["source_file_url"] = first_link(src) if src else None

    lic = kv_field(text, ["源码许可证", "许可证", "代码许可证", "上游许可证"])
    if lic:
        lic = strip_md(re.sub(r"[。.]?\s*\[许可证全文\]\([^)]*\)", "", lic)).rstrip("。 ")
    info["license"] = lic or None

    info["repro_flag"] = bool(re.search(r"照论文复现", text[:400]))
    info["port_flag"] = "移植" in text          # README 自称从别的框架移植
    info["aifeng"] = "AI缝合术" in head
    info["verification"] = summarize_verification(text) if text else None
    m = re.search(r"\((?:[A-Za-z]+ )?(\d{4})\)", pys[0].name) if pys else None
    info["py_year"] = int(m.group(1)) if m else None
    m = re.search(r"\(([A-Za-z][A-Za-z ]*?)\s+\d{4}\)", pys[0].name) if pys else None
    info["py_venue"] = m.group(1) if m else None
    if info["repro_flag"] or "论文复现" in path.rstrip("/").split("/")[-1]:
        info["code"] = {p.name: read(p) for p in pys}   # 照论文复现的代码是自己写的，可以展示
    return info


# ---------------------------------------------------------------- 组装

def source_type(path: str, idx: dict | None, mod: dict, q: dict | None) -> str:
    """作者原版：取自作者或官方框架仓库的固定提交；官方移植：同上但 README 写明换了框架；
    照论文复现：没有官方代码，照论文写的；第三方整理：AI缝合术等转载；其余记为来源未标明。"""
    folder = path.rstrip("/").split("/")[-1]
    if "论文复现" in folder or mod.get("repro_flag"):
        return "repro"
    official = ("官方原版" in folder
                or (mod.get("readme") and mod.get("commit") and (mod.get("repo") or (q or {}).get("repo")))
                or (q is not None and q["queue"] == "main" and q["status"] == "已收"))
    if official:
        return "port" if mod.get("port_flag") else "author"
    if mod.get("aifeng"):
        return "third"
    src = (idx or {}).get("index_source") or ""
    if src.startswith("官方代码") or src.startswith("改写自官方代码"):
        return "author"
    if src.startswith("按论文自行复现"):
        return "repro"
    if src:
        return "third"
    return "unknown"


def hall_of(path: str) -> tuple[str | None, str | None]:
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != "论文复现":
        return None, None
    field = parts[1]
    task = parts[2] if field == "计算机视觉" and len(parts) >= 4 else None
    return field, task


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def build(public: bool = False) -> tuple[dict, dict]:
    ext = load_extend_log()
    index = load_index()
    queue = load_queue(ext)
    repro = load_repro_queue(ext)
    verify_log = load_verify_log()
    rows = queue + repro
    q_by_path = defaultdict(list)
    for q in rows:
        if q.get("path"):
            q_by_path[q["path"]].append(q)

    # 1. 入选的库内模块：模块类型含「注意力」，或者收集队列的备注点名了它的目录。
    chosen = [r for r in index if "注意力" in r["module_type"] or r["path"] in q_by_path]
    idx_paths = {r["path"] for r in chosen}

    # 2. 每个库内模块一份「馆藏副本」；队列写了已收、INDEX 还没登记的目录也算
    copies = []
    for r in chosen:
        qs = q_by_path.get(r["path"], [])
        copies.append(dict(idx=r, mod=read_module_dir(r["path"]), q=qs[0] if qs else None, path=r["path"]))
    for path, qs in q_by_path.items():
        if path not in idx_paths and any(q["status"] in ("已收", "已复现") for q in qs) and (LIB / path).is_dir():
            copies.append(dict(idx=None, mod=read_module_dir(path), q=qs[0], path=path))
            idx_paths.add(path)

    # 3. 同一篇论文、同一模块名的副本和队列记录并成一件展品
    uf = UF()

    def keys(en, arx, title):
        bn = base_name(en or "").lower()
        ks = []
        if arx:
            ks.append(f"ax:{arx}|{bn}")
        tk = norm_title(title)
        if tk:
            ks.append(f"t:{tk}|{bn}")
        return ks

    for i, c in enumerate(copies):
        idx, mod, q = c["idx"], c["mod"], c["q"]
        node = f"c{i}"
        uf.union(node, f"path:{c['path']}")
        en = (idx or {}).get("name_en") or (q or {}).get("name_en")
        for k in keys(en, (q or {}).get("arxiv") or mod.get("arxiv"),
                      (q or {}).get("title") or mod.get("title") or (idx or {}).get("title")):
            uf.union(node, k)
    for q in rows:
        node = f"q:{q['queue']}:{q['no']}"
        uf.union(node, node)
        if q.get("path") and q["path"] in idx_paths:
            uf.union(node, f"path:{q['path']}")
        for k in keys(q["name_en"], q.get("arxiv"), q.get("title")):
            uf.union(node, k)
    groups = defaultdict(lambda: ([], []))
    for i, c in enumerate(copies):
        groups[uf.find(f"c{i}")][0].append(c)
    for q in rows:
        groups[uf.find(f"q:{q['queue']}:{q['no']}")][1].append(q)

    exhibits = []
    for cs, qs in groups.values():
        exhibits.append(assemble(cs, qs, verify_log) if cs else assemble_pending(qs))

    # 5. 唯一编号：年份 + 名称
    seen = Counter()
    for ex in sorted(exhibits, key=lambda e: (e["year"] or 9999, e["name_en"].lower())):
        slug = re.sub(r"[^A-Za-z0-9]+", "-", ex["name_en"]).strip("-") or "x"
        sid = f"{ex['year'] or 'na'}-{slug}"
        seen[sid] += 1
        ex["id"] = sid if seen[sid] == 1 else f"{sid}-{seen[sid]}"

    edges = build_lineage(exhibits)
    story = apply_curation(exhibits, public)      # 在谱系之后：谱系的「备注写明」规则只看队列备注，不看手写简介
    halls = build_halls(exhibits, ext)
    census = build_census(exhibits, queue, repro, ext)
    code = {}
    for ex in exhibits:
        for cp in ex["copies"]:
            if "_codetext" in cp:
                code[cp["path"]] = cp.pop("_codetext")

    return dict(
        generated=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        sources=[str(p.relative_to(LIB)).replace("\\", "/") for p in (INDEX, QUEUE, REPRO_QUEUE, VERIFY_LOG, EXTEND_LOG)],
        source_types=SOURCE_TYPES, directions=ext["directions"], field_en=FIELD_EN,
        exhibits=sorted(exhibits, key=lambda e: (e["year"] or 9999, e["name_en"].lower())),
        edges=edges, halls=halls, census=census, graph=build_graph(exhibits, edges, ext),
        story=story, public=public, contact=load_curation_json(CURATION / "site.json").get("contact") or None, citation_graph=build_citation_graph(exhibits),
        paper_dates=build_paper_dates(exhibits),
    ), code


def pick(*vals):
    for v in vals:
        if v not in (None, "", [], {}):
            return v
    return None


def assemble(cs: list[dict], qs: list[dict], verify_log: dict) -> dict:
    # 主副本：作者原版 > 官方移植 > 照论文复现 > 其他；有 README 的优先
    order = {"author": 0, "port": 1, "repro": 2, "third": 3, "unknown": 4}
    cps = []
    for c in cs:
        idx, mod, q = c["idx"], c["mod"], c["q"]
        path = c["path"]
        st = source_type(path, idx, mod, q)
        ver = mod.get("verification")
        ver_src = "README" if ver else None
        if st == "repro":
            name = (q or {}).get("name_en") or (idx or {}).get("name_en", "")
            lv = None
            for k, v in verify_log.items():
                if k.replace(" ", "").lower() in (name.replace(" ", "").lower(), base_name(name).replace(" ", "").lower()):
                    lv = v
            if lv:
                ver, ver_src = lv, "验证记录.md"
            elif q and q.get("verify"):
                ver, ver_src = q["verify"], "队列-论文复现.md"
        field, task = hall_of(path)
        cp = dict(
            path=path, source_type=st, readme=mod.get("readme", False),
            repo=pick(mod.get("repo"), (q or {}).get("repo")),
            repo_url=pick(mod.get("repo_url"), (q or {}).get("repo_url")),
            commit=mod.get("commit"),
            source_file_url=pick(mod.get("source_file_url"), (q or {}).get("source_file_url")),
            license=pick(mod.get("license"), (q or {}).get("license")),
            verification=ver, verification_source=ver_src,
            index_source=(idx or {}).get("index_source"),
            has_pdf=(idx or {}).get("has_pdf"), field=field, task=task,
            name_zh=(idx or {}).get("name_zh"), name_en=(idx or {}).get("name_en") or (q or {}).get("name_en"),
            in_index=idx is not None,
        )
        if mod.get("code"):
            cp["_codetext"] = mod["code"]
            cp["code_files"] = list(mod["code"].keys())
        cps.append((order[st] + (0 if mod.get("readme") else 0.5), cp, c))
    cps.sort(key=lambda x: x[0])
    main_cp = cps[0][1]
    paths = {c["path"] for c in cs}
    q = primary_row(qs, paths)
    idx = next((c["idx"] for _, _, c in cps if c["idx"]), None)
    mods = [c["mod"] for _, _, c in cps]

    # 年份和出处：队列 > README 出处 > INDEX 论文出处 > arXiv 编号 > 文件名
    year = venue = None
    ysrc = None
    cand = []
    if q and q.get("year"):
        cand.append((q["year"], q["venue"], "队列"))
    for m in mods:
        y, v = parse_venue(m.get("venue_raw"))
        if y:
            cand.append((y, v, "README"))
    for _, cp, c in cps:
        if c["idx"]:
            y, v = parse_venue(c["idx"]["venue_raw"])
            if y:
                cand.append((y, v, "INDEX"))
    arx = pick(q and q.get("arxiv"), *[m.get("arxiv") for m in mods])
    if arx and year_from_arxiv(arx):
        cand.append((year_from_arxiv(arx), None, "arXiv 编号"))
    for m in mods:
        if m.get("py_year"):
            cand.append((m["py_year"], m.get("py_venue"), "代码文件名"))
    if cand:
        year, venue, ysrc = cand[0]
        if not venue:
            venue = next((v for y, v, _ in cand if y == year and v), None)
    title = pick(q and q.get("title"), *[m.get("title") for m in mods], idx and idx.get("title"))
    fields = sorted({(cp["field"], cp["task"]) for _, cp, _ in cps if cp["field"]})
    if not fields and q:
        f, t = hall_of(q["hall_dir"] + "x/")
        if f:
            fields = [(f, t)]
    ex = dict(
        name_en=base_name(pick(idx and idx["name_en"], q and q["name_en"]) or "?"),
        name_zh=pick(*[re.sub(r"（.*?）$", "", cp["name_zh"] or "") for _, cp, _ in cps]) or None,
        title=title, year=year, venue=venue, year_source=ysrc,
        authors=pick(*[m.get("authors") for m in mods]),
        arxiv=arx, doi=pick(q and q.get("doi"), *[m.get("doi") for m in mods]),
        paper_url=pick(q and q.get("paper_url"), *[m.get("paper_url") for m in mods]),
        module_type=idx["module_type"] if idx else None,
        domain=idx["domain"] if idx else None,
        halls=[{"field": f, "task": t} for f, t in fields],
        direction=q.get("direction") if q else None,
        status="collected",
        queue=[queue_ref(r) for r in sorted(qs, key=lambda r: (r["queue"], r["no"]))],
        mechanism=mechanism_of(q, qs),
        formula=None,
        copies=[cp for _, cp, _ in cps],
    )
    ex["mechanism_source"] = "队列备注" if ex["mechanism"] else None
    ex["source_type"] = main_cp["source_type"]
    ex["license"] = license_key(main_cp["license"])
    ex["license_note"] = main_cp["license"]
    ex["guo"] = pick(*[guo_of(r["note"]) for r in qs])
    ex["repo"] = main_cp["repo"]
    ex["repo_url"] = main_cp["repo_url"]
    ex["verification"] = main_cp["verification"]
    ex["missing"] = missing_fields(ex)
    return ex


def mechanism_of(q: dict | None, qs: list[dict]) -> str | None:
    rows = ([q] if q else []) + sorted(qs, key=lambda r: r["status"] == "跳过")
    return pick(*[r.get("mechanism") for r in rows])


def queue_ref(r: dict) -> dict:
    return dict(queue=r["queue"], no=r["no"], status=r["status"], segment=r["segment"],
                note=r["note"] if r["status"] == "跳过" else None)


def primary_row(qs: list[dict], paths: set | None = None) -> dict | None:
    """取一件展品的主队列记录：点名了馆藏目录的已收记录优先，其次是序号最大的记录。"""
    if not qs:
        return None
    hit = [r for r in qs if paths and r.get("path") in paths and r["status"] in ("已收", "已复现")]
    return hit[0] if hit else latest_row(qs)


def latest_row(qs: list[dict]) -> dict:
    """状态走得最远的记录；同状态取主队列、序号大的。先跳过、后转去复现的条目以复现队列为准。"""
    rank = {"已收": 4, "已复现": 4, "待收": 3, "待复现": 3, "候选": 2, "跳过": 1}
    return max(qs, key=lambda r: (rank.get(r["status"], 0), r["queue"] == "main", r["no"]))


def assemble_pending(qs: list[dict]) -> dict:
    q = latest_row(qs)
    st = {"待收": "pending", "待复现": "pending", "候选": "candidate", "跳过": "skipped",
          "已收": "pending", "已复现": "pending"}[q["status"]]
    f, t = hall_of(q["hall_dir"].rstrip("/") + "/x")
    lic = pick(*[r.get("license") for r in [q] + qs])
    ex = dict(
        name_en=q["name_en"], name_zh=None, title=q["title"], year=q["year"], venue=q["venue"],
        year_source="队列" if q["year"] else None, authors=None,
        arxiv=q["arxiv"], doi=q["doi"], paper_url=q["paper_url"], module_type=None, domain=None,
        halls=[{"field": f, "task": t}] if f else [], direction=pick(*[r.get("direction") for r in qs]),
        status=st, queue=[queue_ref(r) for r in sorted(qs, key=lambda r: (r["queue"], r["no"]))],
        mechanism=mechanism_of(q, qs),
        skip_reason=q["note"] if st == "skipped" else None,
        formula=None, copies=[],
        source_type=None, license=license_key(lic), license_note=lic,
        repo=pick(*[r.get("repo") for r in [q] + qs]), repo_url=pick(*[r.get("repo_url") for r in [q] + qs]), verification=None, guo=guo_of(q["note"]),
        planned_source_type=("repro" if q["queue"] == "repro" else ("author" if q.get("repo") else None)),
    )
    ex["mechanism_source"] = "队列备注" if ex["mechanism"] else None
    ex["missing"] = missing_fields(ex)
    return ex


def missing_fields(ex: dict) -> list[str]:
    need = ["name_zh", "title", "year", "venue", "mechanism", "formula"]
    if ex["status"] == "collected":
        need.append("verification")
        if ex["source_type"] != "repro":      # 照论文复现是自己写的，没有上游仓库和许可证
            need += ["license", "repo"]
    link = ["paper_link"] if not (ex.get("arxiv") or ex.get("doi") or ex.get("paper_url")) else []
    return [k for k in need if not ex.get(k)] + link


# ---------------------------------------------------------------- 馆长手写层

CURATION = HERE / "curation"
FIG_DIR = HERE / "site" / "figures"


def load_curation_json(p: Path) -> dict:
    """手写层由别的会话陆续写出。文件不存在时返回空表，写到一半读不成 JSON 时跳过并提示。"""
    if not p.exists():
        return {}
    try:
        return json.loads(read(p))
    except json.JSONDecodeError as err:
        print(f"跳过 curation/{p.name}：JSON 不完整（{err}）", file=sys.stderr)
        return {}


def build_citation_graph(exhibits: list[dict]) -> dict:
    data = load_curation_json(CURATION / "paper_citations.json")
    lookup = data.get("identifiers", {})
    papers = defaultdict(list)
    unmatched = {}
    for exhibit in exhibits:
        ids = identifiers(exhibit)
        works = {lookup[doi] for doi in ids if doi in lookup}
        if len(works) == 1:
            papers[works.pop()].append(exhibit["id"])
        else:
            unmatched[exhibit["id"]] = "ambiguous" if works else "unresolved" if ids else "no_identifier"

    references = data.get("references", {})
    edges = [
        dict(citing=citing, cited=cited, source_url=f"https://api.openalex.org/works/{citing}?select=id,referenced_works")
        for citing in sorted(papers)
        for cited in references.get(citing, [])
        if cited in papers and cited != citing
    ]
    return dict(provider="OpenAlex", license="CC0-1.0", works=dict(sorted(papers.items())),
                edges=edges, unmatched=unmatched)


def build_paper_dates(exhibits: list[dict]) -> dict:
    data = load_curation_json(CURATION / "paper_dates.json")
    dates = data.get("arxiv_v1_submitted", {})
    arxiv = {exhibit["arxiv"] for exhibit in exhibits if exhibit.get("arxiv")}
    return {
        aid: dict(date=dates[aid], kind="arxiv_v1_submitted",
                  source_url=f"https://arxiv.org/abs/{aid}v1",
                  metadata_url=f"https://api.datacite.org/dois/10.48550/arxiv.{aid}")
        for aid in sorted(arxiv & dates.keys())
    }


def is_cc(lic: str | None) -> bool:
    """能随开源仓库再分发的许可。带 ND 的不算：配图时裁过白边、拼过子图，可能算改动。"""
    return bool(lic) and bool(re.search(r"creativecommons\.org|^CC[- ]?(BY|0)", lic, re.I)) and "-nd" not in lic.lower()


def load_story() -> dict | None:
    """导览稿。馆长的定稿在 curation/story_rooms/：00-thesis.json 是开场白，其余一室一个文件。

    每室的 sections 是一段展墙文字加它讲到的展品。另外生成平铺的 anchors 和 body，
    给只关心「这一室有哪些展品」的代码用。目录不存在时退回旧的 story.json。
    """
    rooms_dir = CURATION / "story_rooms"
    if not rooms_dir.is_dir():
        return load_curation_json(CURATION / "story.json") or None
    story = dict(load_curation_json(rooms_dir / "00-thesis.json"))
    story["chapters"] = []
    for p in sorted(rooms_dir.glob("[0-9][0-9]-*.json")):
        if p.name == "00-thesis.json":
            continue
        room = load_curation_json(p)
        if not room:
            continue
        room["anchors"] = [a for s in room["sections"] for a in s["anchors"]]
        for lang in ("zh", "en"):
            room[f"body_{lang}"] = "\n\n".join(s[f"text_{lang}"] for s in room["sections"])
        story["chapters"].append(room)
    return story


def apply_curation(exhibits: list[dict], public: bool) -> dict | None:
    """把简介、英文文案和论文配图并进展品，再生成英文模式用的 en 字段。返回导览稿。"""
    texts = {}
    for p in sorted(CURATION.glob("texts.part*.json")):
        texts.update(load_curation_json(p))
    figures = load_curation_json(CURATION / "figures.json")
    house = load_curation_json(CURATION / "figures_house.json")
    story = load_story()
    rooms = load_curation_json(CURATION / "rooms.json")     # 馆长逐件定的展室。没有的展品由总图按领域和年份估
    for e in exhibits:
        if e["id"] in rooms:
            e["room"] = rooms[e["id"]]
        t = texts.get(e["id"]) or {}
        if (t.get("mechanism_zh") or "").strip():
            e["mechanism"] = t["mechanism_zh"].strip()
            e["mechanism_source"] = MECH_SOURCE_CURATOR
        if t.get("basis"):
            e["mechanism_basis"] = t["basis"]
        f = figures.get(e["id"])
        if f and f.get("file") and (not public or is_cc(f.get("license"))):
            e["figure"] = {k: f.get(k) for k in ("file", "fig_no", "caption", "source_url", "license")}
        elif e["id"] in house and (FIG_DIR.parent / house[e["id"]]["file"]).is_file():
            h = house[e["id"]]       # 论文没有结构图的展品，用馆内按论文和代码画的图
            e["figure"] = dict(file=h["file"], fig_no=None, caption=h.get("caption_en"), caption_zh=h.get("caption_zh"), source_url=None, license=None, house=True)
        e["missing"] = missing_fields(e)
        lic_key = e.get("license")
        en = dict(
            title=title_en(e.get("title")), venue=table_en(VENUE_EN, "venue", e.get("venue")),
            authors=authors_en(e.get("authors")), mechanism=ascii_only(t.get("mechanism_en")),
            verification=ascii_only(t.get("check_en")) if e.get("verification") else None,
            license=license_en(lic_key, e.get("license_note")),
            module_type=table_en(MTYPE_EN, "module_type", e.get("module_type")),
            domain=table_en(DOMAIN_EN, "domain", e.get("domain")), guo=guo_en(e.get("guo")),
            year_source=table_en(YEAR_SOURCE_EN, "year_source", e.get("year_source")),
        )
        e["en"] = {k: v for k, v in en.items() if v}
        for c in e["copies"]:
            cen = dict(
                name=ascii_only(re.sub(r"-(官方原版|论文复现)$", "", c.get("name_en") or "")),
                license=license_en(license_key(c.get("license")), c.get("license")),
                verification=e["en"].get("verification") if c.get("verification") and c["verification"] == e.get("verification") else None,
                verification_source=table_en(VER_SOURCE_EN, "verification_source", c.get("verification_source")),
            )
            c["en"] = {k: v for k, v in cen.items() if v}
    return story


# ---------------------------------------------------------------- 谱系

GENERIC = {"attention", "transformer", "self-attention", "mha", "sa", "ca", "net", "vit", "cnn", "memory",
           "gate", "gated", "linear", "sparse", "local", "global", "cross", "position", "conv", "mlp",
           "block", "module", "network", "networks", "lstm", "rnn", "unet", "u-net", "pointer", "relative"}
# 由普通英文词组成的模块名，在别的论文题目里出现多半只是用词，不算点名。
TITLE_STOP = {"based", "sparse transformer", "memory networks", "hydra"}
REL_VERB = r"(改自|改进|扩展|延伸|继承|沿用|替换|源自|推广|简化|变体|基础上|基于|取代|升级|改写)"


def build_lineage(exhibits: list[dict]) -> list[dict]:
    names = {}
    for e in exhibits:
        n = e["name_en"]
        if len(n) >= 3 and n.lower() not in GENERIC:
            names.setdefault(n, []).append(e)
    edges, seen = [], set()

    def add(child, parent, rule, evidence, evidence_en):
        if child is parent or (child["id"], parent["id"]) in seen:
            return
        if child["year"] and parent["year"] and parent["year"] > child["year"]:
            return
        seen.add((child["id"], parent["id"]))
        edges.append(dict(source=parent["id"], target=child["id"], rule=rule, evidence=evidence, evidence_en=evidence_en))

    def mentions(text, name):
        return re.search(rf"(?<![A-Za-z0-9-]){re.escape(name)}(?![A-Za-z0-9])", text) is not None

    for e in exhibits:
        # 规则 1：名称带版本号，前一版也在馆
        m = re.fullmatch(r"(.+?)[- ]?(?:v|V)?(\d+|\+\+)", e["name_en"])
        if m and (m.group(2) == "++" or int(m.group(2)) >= 2):
            stem = m.group(1).rstrip("- ")
            for cand in names.get(stem, []) + names.get(stem + "v1", []) + names.get(stem + "-1", []):
                add(e, cand, "名称版本号", f"{e['name_en']} 是 {cand['name_en']} 的后续版本（名称编号）",
                    f"{e['name_en']} follows {cand['name_en']} (version number in the name)")
        # 规则 2：论文题目点名另一件展品。去掉：被更长匹配包住的短匹配、同一篇论文里的另一个模块、
        # 题目开头的模型名恰好是对方名字（同缩写撞名）、普通英文词组成的名字。
        if e.get("title"):
            t = e["title"]
            head = re.split(r"[:：]", t, maxsplit=1)[0].strip() if re.search(r"[:：]", t) else t.split()[0]
            hits = []
            for n, cands in names.items():
                if n == e["name_en"] or len(n) < 4 or n.lower() in TITLE_STOP or head == n:
                    continue
                for m in re.finditer(rf"(?<![A-Za-z0-9-]){re.escape(n)}(?![A-Za-z0-9])", t):
                    hits.append((m.span(), n))
            hits = [(sp, n) for sp, n in hits
                    if not any(o != sp and o[0] <= sp[0] and sp[1] <= o[1] for o, _ in hits)]
            for _, n in hits:
                for c in names[n]:
                    if same_paper(e, c):
                        continue
                    add(e, c, "题目点名", f"论文题目：{t}", f"Paper title: {t}" if ascii_only(t) else None)
        # 规则 3：队列备注里同一句话点名另一件展品，并带关系动词
        note = e.get("mechanism") or ""
        for sent in re.split(r"(?<=。)", note):
            if not re.search(REL_VERB, sent):
                continue
            for n, cands in names.items():
                if n != e["name_en"] and len(n) >= 3 and mentions(sent, n):
                    for c in cands:
                        add(e, c, "备注写明", f"队列备注：{sent.strip()}", None)
    return transitive_reduce(edges)


def same_paper(a: dict, b: dict) -> bool:
    if a.get("arxiv") and a.get("arxiv") == b.get("arxiv"):
        return True
    ta, tb = norm_title(a.get("title")), norm_title(b.get("title"))
    return bool(ta and ta == tb)


def transitive_reduce(edges: list[dict]) -> list[dict]:
    """A→B→C 已连通时去掉 A→C。"""
    out = defaultdict(set)
    for g in edges:
        out[g["source"]].add(g["target"])

    def reach(a, goal, skip):
        stack, seen = [x for x in out[a] if x != skip], set()
        while stack:
            x = stack.pop()
            if x == goal:
                return True
            if x in seen:
                continue
            seen.add(x)
            stack.extend(out[x])
        return False

    return [g for g in edges if not reach(g["source"], g["target"], g["target"])]


# ---------------------------------------------------------------- 展厅与普查

VENUE_ALIAS = {"ARXIV": "arXiv", "NIPS": "NeurIPS", "IEEE TPAMI": "TPAMI", "ECCV Workshops": "ECCVW",
               "ICCV Workshops": "ICCVW", "EMNLP-IJCNLP": "EMNLP", "EMNLP Findings": "Findings of EMNLP"}


def venue_key(v: str | None) -> str | None:
    if not v:
        return None
    v = re.sub(r"\s*\([^)]*$", "", v).strip()        # 去掉解析时截断的半个括号
    return VENUE_ALIAS.get(v, v) or None


def build_graph(exhibits: list[dict], edges: list[dict], ext: dict) -> dict:
    """知识图谱：展品和它们共有的展厅、扫描方向、出处、仓库、年份。边只用已有字段，不推断新关系。"""
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def hub(nid, kind, label, label_en=None, **kw):
        if nid not in nodes:
            nodes[nid] = dict(id=nid, kind=kind, label=label, label_en=label_en or label, **kw)
        return nid

    repo_count = Counter()
    for e in exhibits:
        for r in {c["repo"] for c in e["copies"] if c.get("repo")} | ({e["repo"]} if e.get("repo") else set()):
            repo_count[r] += 1

    paper_groups = defaultdict(list)
    for e in exhibits:
        nodes[e["id"]] = dict(id=e["id"], kind="exhibit", label=e["name_en"], label_zh=e.get("name_zh"),
                              status=e["status"], src=e.get("source_type"), year=e.get("year"))
        for h in e["halls"]:
            fid = hub(f"hall:{h['field']}", "hall", h["field"], FIELD_EN.get(h["field"]))
            if h["task"]:
                tid = hub(f"hall:{h['field']}/{h['task']}", "hall", h["task"], FIELD_EN.get(h["task"]), parent=fid)
                links.append(dict(source=e["id"], target=tid, kind="hall"))
            else:
                links.append(dict(source=e["id"], target=fid, kind="hall"))
        if e.get("direction"):
            d = ext["directions"][e["direction"]]
            did = hub(f"dir:{e['direction']}", "direction", f"{e['direction']}. {d['zh']}", f"{e['direction']}. {d.get('en') or d['zh']}")
            links.append(dict(source=e["id"], target=did, kind="direction"))
        v = venue_key(e.get("venue"))
        if v:
            links.append(dict(source=e["id"], target=hub(f"venue:{v}", "venue", v, VENUE_EN.get(v)), kind="venue"))
        for r in sorted({c["repo"] for c in e["copies"] if c.get("repo")} | ({e["repo"]} if e.get("repo") else set())):
            if repo_count[r] >= 2:                     # 只给至少两件展品共用的仓库建节点
                links.append(dict(source=e["id"], target=hub(f"repo:{r}", "repo", r), kind="repo"))
        if e.get("year"):
            links.append(dict(source=e["id"], target=hub(f"year:{e['year']}", "year", str(e["year"])), kind="year"))
        key = e.get("arxiv") or norm_title(e.get("title"))
        if key:
            paper_groups[key].append(e["id"])

    # 子任务展厅挂到所属领域
    for n in list(nodes.values()):
        if n["kind"] == "hall" and n.get("parent"):
            links.append(dict(source=n["id"], target=n["parent"], kind="hall"))
    # 同一篇论文的不同展品首尾相连
    for ids in paper_groups.values():
        for a, b in zip(ids, ids[1:]):
            links.append(dict(source=a, target=b, kind="paper"))
    for g in edges:
        links.append(dict(source=g["source"], target=g["target"], kind="lineage", rule=g["rule"]))
    return dict(nodes=list(nodes.values()), links=links)


def build_halls(exhibits, ext):
    by_field = defaultdict(lambda: defaultdict(int))
    for e in exhibits:
        for h in e["halls"]:
            by_field[h["field"]][h["task"] or ""] += 1
    fields = []
    for f, tasks in sorted(by_field.items(), key=lambda x: -sum(x[1].values())):
        fields.append(dict(field=f, en=FIELD_EN.get(f), count=sum(tasks.values()),
                           tasks=[dict(task=t, en=FIELD_EN.get(t), count=n)
                                  for t, n in sorted(tasks.items(), key=lambda x: -x[1]) if t]))
    dirs = []
    for k in sorted(ext["directions"]):
        d = ext["directions"][k]
        n = sum(1 for e in exhibits if e.get("direction") == k)
        dirs.append(dict(key=k, zh=d["zh"], en=d.get("en"), scanned=d.get("scanned", False), count=n))
    return dict(fields=fields, directions=dirs)


def build_census(exhibits, queue, repro, ext):
    rows = []
    for k in sorted(ext["directions"]):
        d = ext["directions"][k]
        es = [e for e in exhibits if e.get("direction") == k]
        rows.append(dict(key=k, zh=d["zh"], en=d.get("en"), scanned=d.get("scanned", False),
                         sources=d.get("sources", []),
                         collected=sum(e["status"] == "collected" for e in es),
                         pending=sum(e["status"] == "pending" for e in es),
                         candidate=sum(e["status"] == "candidate" for e in es),
                         skipped=sum(e["status"] == "skipped" for e in es)))
    seg = defaultdict(Counter)
    for q in queue:
        seg[q["segment"]][q["status"]] += 1
    rseg = Counter(q["status"] for q in repro)
    skipped = [dict(name=q["name_en"], queue=q["queue"], no=q["no"], segment=q["segment"],
                    year=q["year"], reason=q["note"]) for q in queue + repro if q["status"] == "跳过"]
    fields = defaultdict(Counter)
    for e in exhibits:
        f = e["halls"][0]["field"] if e["halls"] else "未归属"
        fields[f][e["status"]] += 1
    return dict(directions=rows, segments={k: dict(v) for k, v in sorted(seg.items())},
                repro=dict(rseg), skipped=skipped, no_official_code=load_no_code_list(),
                fields={k: dict(v) for k, v in fields.items()}, pending_directions=ext["pending"])


def main(argv: list[str]) -> None:
    public = "--public" in argv
    data, code = build(public)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "museum.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "code.json").write_text(json.dumps(code, ensure_ascii=False), encoding="utf-8")
    ex = data["exhibits"]
    st = Counter(e["status"] for e in ex)
    miss = sum(1 for e in ex if e["status"] == "collected" and set(e["missing"]) - {"formula"})
    mc = Counter(m for e in ex if e["status"] == "collected" for m in e["missing"])
    print(f"展品 {len(ex)} 件：" + "，".join(f"{k} {v}" for k, v in st.items()))
    print(f"馆藏副本 {sum(len(e['copies']) for e in ex)} 份")
    print(f"已入藏且缺公式以外字段的展品 {miss} 件；按字段：{dict(mc)}")
    print(f"谱系边 {len(data['edges'])} 条：{dict(Counter(e['rule'] for e in data['edges']))}")
    print(f"照论文复现代码 {len(code)} 份")
    figs = [e["figure"] for e in ex if e.get("figure")]
    print(f"手写简介 {sum(e.get('mechanism_source') == MECH_SOURCE_CURATOR for e in ex)} 件，英文简介 {sum('mechanism' in e['en'] for e in ex)} 件，"
          f"论文配图 {len(figs)} 张，导览 {len((data['story'] or {}).get('chapters', []))} 室")
    for kind, vals in sorted(unmapped.items()):
        print(f"英文对照表缺 {kind} 的 {len(vals)} 个取值，英文模式不显示：{'、'.join(sorted(vals))}")
    if public and FIG_DIR.is_dir():
        used = {Path(f["file"]).name for f in figs}
        extra = [p.name for p in FIG_DIR.iterdir() if p.is_file() and p.name not in used]
        print(f"--public：只带 Creative Commons 许可的 {len(figs)} 张图。site/figures/ 里另有 {len(extra)} 个文件没有引用，上传前排除它们。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
