"""导出一份可以公开的仓库副本到 dist/repo/。只在本机生成文件，不发布，不推送。

默认带全部论文图，和线上站点一样当作介绍论文时的引用，逐图注明出处（馆主 2026-11-25 定）。
加 --cc-only 时只带作者以可再分发的许可发布的图（CC BY、CC BY-SA、CC BY-NC-SA、CC0，不含 ND），
其余的图由拿到仓库的人运行 fetch_figures.py 从 arXiv 取。

用法：python export_repo.py [--cc-only]        全部通过时退出码为 0
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "dist" / "repo"
sys.path.insert(0, str(HERE))
import build_data as bd  # noqa: E402

# 不进公开仓库的东西：派工的工单、只供馆长参考的调研、原型、生成的数据（下面另行生成公开版）
SKIP = [
    r"^curation/工单", r"^docs/暗色哥特气质", r"^docs/screenshots/", r"^prototypes/", r"^site/figures/",
    r"^site/data/", r"^HANDOFF\.md$", r"^dist/",
]
# 公开的文件里不该出现的字样：本机路径和用户名
LEAKS = re.compile("User" + r"Data[\\/]|[A-Za-z]:[\\/]Users[\\/]|[\\/]home[\\/]" + "osc" + "ar")   # 拼起来写，免得这一行自己被查出来


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cc_only = "--cc-only" in sys.argv
    tracked = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files"], cwd=HERE, capture_output=True, text=True, encoding="utf-8", check=True).stdout.split("\n")
    files = [f for f in tracked if f and not any(re.search(p, f) for p in SKIP)]
    if OUT.exists():          # 留着 .git 和 .gitignore：dist/repo 就是公开仓库的工作区，导出后在里面提交、推送
        for p in OUT.iterdir():
            if p.name not in {".git", ".gitignore"}:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    for f in files:
        dst = OUT / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / f, dst)

    # 能再分发的论文图
    figures = json.loads((HERE / "curation" / "figures.json").read_text(encoding="utf-8"))
    keep = {k: v for k, v in figures.items() if v.get("file") and (not cc_only or bd.is_cc(v.get("license")))}
    (OUT / "site" / "figures").mkdir(parents=True, exist_ok=True)
    missing = []
    for v in keep.values():
        src = HERE / "site" / v["file"]
        if src.exists():
            shutil.copy2(src, OUT / "site" / v["file"])
        else:
            missing.append(v["file"])

    # 公开版的数据：只引用上面这些图。生成完把本机的数据恢复成完整版
    try:
        if cc_only:
            subprocess.run([sys.executable, str(HERE / "build_data.py"), "--public"], cwd=HERE, check=True, capture_output=True)
        shutil.copytree(HERE / "site" / "data", OUT / "site" / "data")
    finally:
        if cc_only:
            subprocess.run([sys.executable, str(HERE / "build_data.py")], cwd=HERE, check=True, capture_output=True)

    data = json.loads((OUT / "site" / "data" / "museum.json").read_text(encoding="utf-8"))
    referenced = {e["figure"]["file"] for e in data["exhibits"] if e.get("figure")}
    shipped = {p.relative_to(OUT / "site").as_posix() for p in (OUT / "site" / "figures").glob("*")}
    leaks = []
    for p in OUT.rglob("*"):
        if p.is_file() and "vendor" not in p.parts and ".git" not in p.parts and p.name != "site.json" and p.suffix in {".py", ".js", ".css", ".html", ".md", ".txt", ".json", ".mjs", ".example"} and p.stat().st_size < 3_000_000:
            m = LEAKS.search(p.read_text(encoding="utf-8", errors="ignore"))
            if m:
                leaks.append(f"{p.relative_to(OUT).as_posix()}: {m.group(0)}")
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file() and ".git" not in p.parts)
    print(f"导出到 {OUT.relative_to(HERE).as_posix()}：{sum(1 for p in OUT.rglob('*') if p.is_file() and '.git' not in p.parts)} 个文件，{size / 1048576:.1f} MB")
    print(f"论文图：全馆 {len(figures)} 张，仓库带 {len(shipped)} 张，没带的 {len(figures) - len(shipped)} 张")
    problems = []
    if missing:
        problems.append(f"清单里有但磁盘上没有的图 {len(missing)} 张：{missing[:5]}")
    if referenced - shipped:
        problems.append(f"公开数据引用了没带的图 {len(referenced - shipped)} 张：{sorted(referenced - shipped)[:5]}")
    if leaks:
        problems.append(f"公开文件里有本机痕迹 {len(leaks)} 处：{leaks[:8]}")
    if not (OUT / "LICENSE").exists():
        problems.append("还没有 LICENSE 文件。许可证由馆主定了以后放进仓库根目录")
    for p in problems:
        print("注意：" + p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
