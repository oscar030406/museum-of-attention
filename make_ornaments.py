# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely>=2.0"]
# ///
"""生成画框的镶嵌边带 site/assets/frame-light.svg 和 frame-dark.svg，以及馆徽。用法：uv run make_ornaments.py

边带是九宫格：四个角各一块，四条边各一块，中间留空。样式表用 border-image 把它绕在论文图外面，
边上的那一块沿边重复，所以图多大都合适。纹样由几何运算得到：边上是一排四叶饰的窗洞，
窗洞之间是小菱形，四角是嵌着六叶饰的圆章。颜色是平涂的，按浅色和深色各出一个文件。
"""
from __future__ import annotations

import math
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parent / "site" / "assets"
T = 48                                    # 一块的边长
PALETTES = {
    # band 边带底色，line 线，glass 窗洞里的玻璃，gem 菱形和圆章的底
    "light": dict(band="#b8892b", line="#17140f", glass="#7d1a2b", gem="#1f3c73"),
    "dark": dict(band="#171a2e", line="#c4c6dc", glass="#3344aa", gem="#7a45b8"),
}


def foil(cx: float, cy: float, lobes: int, lobe_r: float, off: float, turn: float = 0.0):
    parts = [Point(cx + off * math.sin(math.radians(turn + k * 360 / lobes)), cy - off * math.cos(math.radians(turn + k * 360 / lobes))).buffer(lobe_r, 32) for k in range(lobes)]
    return unary_union(parts + [Point(cx, cy).buffer(off * 0.7, 32)])


def d_of(g) -> str:
    g = g.simplify(0.15)
    geoms = [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    return "".join("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in list(p.exterior.coords)[:-1]) + "Z" for p in geoms)


def tiles(c: dict) -> str:
    tile = box(0, 0, T, T)
    quatre = foil(T / 2, T / 2, 4, 7.4, 7.2, turn=45)
    diamonds = unary_union([Polygon([(x - 5.5, T / 2), (x, T / 2 - 5.5), (x + 5.5, T / 2), (x, T / 2 + 5.5)]) for x in (0, T)]).intersection(tile)
    edge = (f'<rect width="{T}" height="{T}" fill="{c["band"]}"/>'
            f'<rect width="{T}" height="3" fill="{c["line"]}"/><rect y="{T - 3}" width="{T}" height="3" fill="{c["line"]}"/>'
            f'<rect y="6" width="{T}" height="1" fill="{c["line"]}"/><rect y="{T - 7}" width="{T}" height="1" fill="{c["line"]}"/>'
            f'<path d="{d_of(quatre)}" fill="{c["glass"]}" stroke="{c["line"]}" stroke-width="1.3"/>'
            f'<path d="{d_of(diamonds)}" fill="{c["gem"]}" stroke="{c["line"]}" stroke-width="1.1"/>')
    medal = Point(T / 2, T / 2).buffer(17.5, 48)
    six = foil(T / 2, T / 2, 6, 5.4, 8.2)
    corner = (f'<rect width="{T}" height="{T}" fill="{c["band"]}"/>'
              f'<rect width="{T}" height="3" fill="{c["line"]}"/><rect width="3" height="{T}" fill="{c["line"]}"/>'
              f'<rect y="6" x="6" width="{T - 6}" height="1" fill="{c["line"]}"/><rect x="6" y="6" width="1" height="{T - 6}" fill="{c["line"]}"/>'
              f'<rect x="{T - 3}" y="{T - 3}" width="3" height="3" fill="{c["line"]}"/>'
              f'<path d="{d_of(medal)}" fill="{c["gem"]}" stroke="{c["line"]}" stroke-width="1.5"/>'
              f'<path d="{d_of(six)}" fill="{c["glass"]}" stroke="{c["line"]}" stroke-width="1.1"/>'
              f'<circle cx="{T / 2}" cy="{T / 2}" r="2.6" fill="{c["band"]}" stroke="{c["line"]}" stroke-width="0.9"/>')
    use = lambda ref, x, y, a: f'<use href="#{ref}" transform="translate({x} {y}) rotate({a} {T / 2} {T / 2})"/>'
    placed = (use("c", 0, 0, 0) + use("e", T, 0, 0) + use("c", 2 * T, 0, 90) + use("e", 2 * T, T, 90)
              + use("c", 2 * T, 2 * T, 180) + use("e", T, 2 * T, 180) + use("c", 0, 2 * T, 270) + use("e", 0, T, 270))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{3 * T}" height="{3 * T}" viewBox="0 0 {3 * T} {3 * T}">'
            f'<defs><g id="e">{edge}</g><g id="c">{corner}</g></defs>{placed}</svg>\n')


def public_domain_ornaments() -> None:
    """把公版纹样（prototypes/gothic/ornaments/，出处见那里的 README）放进站内。

    角花原件是左上角的朝向，另外三个角用镜像得到。样式表把它们当蒙版用，颜色由主题变量给。
    """
    src = OUT.parent.parent / "prototypes" / "gothic" / "ornaments"
    dst = OUT / "ornaments"
    dst.mkdir(exist_ok=True)
    corner = (src / "corner-leaf.svg").read_text(encoding="utf-8")
    head, rest = corner.split(">", 1)
    w, h = (float(v) for v in head.split('viewBox="')[1].split('"')[0].split()[2:])
    flips = {"tl": "", "tr": f"translate({w} 0) scale(-1 1)", "bl": f"translate(0 {h}) scale(1 -1)", "br": f"translate({w} {h}) scale(-1 -1)"}
    for key, tf in flips.items():
        body = rest.rsplit("</svg>", 1)[0]
        (dst / f"corner-{key}.svg").write_text(f'{head}><g transform="{tf}">{body}</g></svg>' if tf else corner, encoding="utf-8")
    for name in ("divider-rosette.svg", "band-foliage.svg", "README.md"):
        (dst / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"ornaments: {len(list(dst.iterdir()))} files")


def emblem() -> None:
    """馆徽：一张 4×4 的因果注意力权重图。

    下三角是能看到的位置，颜色深浅是权重，对角线是每个位置看自己。上三角是被掩码挡住的位置，只画空格子。
    写两处：site/assets/emblem.svg（浏览器标签上的图标，颜色写死，跟着系统的深浅色）和
    site/index.html 里的 <symbol id="emblem">（顶栏用，颜色跟着主题变量）。
    """
    weights = [[1], [.55, 1], [.32, .66, 1], [.3, .42, .66, 1]]
    c, g, lw = 3.7, .7, .55
    m = (20 - 4 * c - 3 * g) / 2
    at = lambda k: m + k * (c + g)
    ghost = "".join(f'<rect x="{at(j) + lw / 2:.2f}" y="{at(i) + lw / 2:.2f}" width="{c - lw:.2f}" height="{c - lw:.2f}"/>' for i in range(4) for j in range(i + 1, 4))
    seen = "".join(f'<rect x="{at(j):.2f}" y="{at(i):.2f}" width="{c}" height="{c}" opacity="{w}"/>' for i, row in enumerate(weights) for j, w in enumerate(row) if i != j)
    diag = "".join(f'<rect x="{at(i):.2f}" y="{at(i):.2f}" width="{c}" height="{c}"/>' for i in range(4))
    lt = PALETTES["light"]
    icon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><style>'
            f'.b{{fill:#ebe5d6}}.s{{fill:{lt["glass"]}}}.g{{fill:none;stroke:{lt["glass"]};stroke-width:{lw};opacity:.45}}.d{{fill:{lt["band"]}}}'
            f'@media (prefers-color-scheme:dark){{.b{{fill:#0a0b13}}.s{{fill:#8795ff}}.g{{stroke:#8795ff}}.d{{fill:#d0558f}}}}'
            f'</style><rect class="b" width="20" height="20" rx="2.5"/><g class="g">{ghost}</g><g class="s">{seen}</g><g class="d">{diag}</g></svg>\n')
    (OUT / "emblem.svg").write_text(icon, encoding="utf-8")
    symbol = ('<symbol id="emblem" viewBox="0 0 20 20">\n'
              f'    <g fill="none" stroke="currentColor" stroke-width="{lw}" opacity=".45">{ghost}</g>\n'
              f'    <g fill="currentColor">{seen}</g>\n'
              f'    <g style="fill:var(--rose)">{diag}</g>\n'
              '  </symbol>')
    page = OUT.parent / "index.html"
    html = page.read_text(encoding="utf-8")
    a, b = html.index('<symbol id="emblem"'), html.index("</symbol>", html.index('<symbol id="emblem"')) + len("</symbol>")
    page.write_text(html[:a] + symbol + html[b:], encoding="utf-8", newline="")
    print(f"emblem.svg {len(icon)} bytes, index.html symbol updated")


def main() -> None:
    emblem()
    public_domain_ornaments()
    for name, colours in PALETTES.items():
        svg = tiles(colours)
        (OUT / f"frame-{name}.svg").write_text(svg, encoding="utf-8")
        print(f"frame-{name}.svg {len(svg)} bytes")


if __name__ == "__main__":
    main()
