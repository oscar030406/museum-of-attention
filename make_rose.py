# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely>=2.0"]
# ///
"""生成首页的玫瑰窗 site/assets/rose.svg。用法：uv run make_rose.py

窗子按哥特花格的作图法由几何运算得到，不手画：
- 八个主窗洞（一室一个）：扇形窗身加等边尖拱窗头，尖拱是两段圆弧相交。
- 窗头之间的四叶饰、外圈的三叶饰、主窗尖上的六叶饰：都是几个圆的并集。
- 每个窗洞先留一圈边条，里面切成菱形小玻璃（铅条分格）。主窗中间留一块圆形的素玻璃放展室编号。
- 中心是一朵多层花瓣的玫瑰，套在八叶饰里。
颜色不写在文件里。每块玻璃只带一个类名，颜色由 style.css 按浅色和深色两套主题给。
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parent / "site" / "assets" / "rose.svg"
N = 8                       # 主窗洞数，等于展室数
R = 505                     # 石圈外半径
rng = random.Random(1128)   # 固定种子，每次生成的文件一样


def polar(r: float, deg: float) -> tuple[float, float]:
    """角度从正上方起，顺时针为正。"""
    a = math.radians(deg)
    return (r * math.sin(a), -r * math.cos(a))


def disc(r: float, deg: float, rad: float):
    return Point(*polar(r, deg)).buffer(rad, 48)


def foil(r: float, deg: float, lobes: int, lobe_r: float, off: float, turn: float = 0.0):
    """n 叶饰：n 个圆绕一个中心排一圈再合并。"""
    cx, cy = polar(r, deg)
    parts = [Point(cx + off * math.sin(math.radians(turn + deg + k * 360 / lobes)),
                   cy - off * math.cos(math.radians(turn + deg + k * 360 / lobes))).buffer(lobe_r, 40) for k in range(lobes)]
    return unary_union(parts + [Point(cx, cy).buffer(off * 0.72, 40)])


def lancet():
    """朝正上方的主窗洞：扇形窗身加尖拱窗头。"""
    alpha, r1, r2 = 20.2, 128.0, 270.0
    body = Polygon([polar(r1, a) for a in frange(-alpha, alpha, 24)] + [polar(r2, a) for a in frange(alpha, -alpha, 24)])
    ax, ay = polar(r2, -alpha)
    bx, by = polar(r2, alpha)
    span = bx - ax
    rho = 0.8 * span                                   # 圆心在起拱线上、半径小于跨度：低一些的尖拱
    head = Point(ax + rho, ay).buffer(rho, 96).intersection(Point(bx - rho, by).buffer(rho, 96)).intersection(box(-600, -600, 600, ay))
    return unary_union([body, head]).buffer(0)


def frange(a: float, b: float, n: int):
    return [a + (b - a) * i / n for i in range(n + 1)]


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def quarries(light, deg: float, size: float):
    """把一个窗洞切成菱形小玻璃。菱形格子跟着窗洞的朝向转。"""
    local = affinity.rotate(light, -deg, origin=(0, 0))
    minx, miny, maxx, maxy = local.bounds
    out = []
    k0, k1 = int((minx + miny) // size) - 2, int((maxx + maxy) // size) + 2
    m0, m1 = int((minx - maxy) // size) - 2, int((maxx - miny) // size) + 2
    for k in range(k0, k1):
        for m in range(m0, m1):
            # 菱形的四个角：u = x + y，v = x - y 的格点
            pts = [((u + v) / 2, (u - v) / 2) for u, v in ((k * size, m * size), ((k + 1) * size, m * size), ((k + 1) * size, (m + 1) * size), (k * size, (m + 1) * size))]
            for p in polys(Polygon(pts).intersection(local)):
                if p.area > size * size * 0.04:
                    out.append(affinity.rotate(p, deg, origin=(0, 0)))
    return out


def d_of(p) -> str:
    p = p.simplify(0.45)          # 圆弧取得很密，输出前去掉看不出差别的点，文件小一个量级

    def ring(coords):
        pts = list(coords)[:-1]
        return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
    return ring(p.exterior.coords) + "".join(ring(i.coords) for i in p.interiors)


def glaze(light, deg: float, fam: str, size: float, band: float, out: list, keep=None):
    """一个窗洞的玻璃：一圈边条，里面是菱形小块。keep 是留作素玻璃的区域。"""
    inner = light.buffer(-band)
    out.append(f'<path class="rim" d="{d_of(light)}"/>')      # 窗洞的轮廓线，比玻璃之间的铅线粗一级
    for p in polys(light.difference(inner)):
        out.append(f'<path class="bd" d="{d_of(p)}"/>')
    field = inner.difference(keep) if keep is not None else inner
    for p in quarries(field, deg, size):
        out.append(f'<path class="f{fam}{rng.choice("1123")}" d="{d_of(p)}"/>')


def main() -> None:
    lights = []                      # 所有窗洞，用来从石圈里挖掉
    body: list[str] = []
    step = 360 / N
    base = lancet()
    for i in range(N):
        deg = i * step
        light = affinity.rotate(base, deg, origin=(0, 0))
        medal = disc(212, deg, 33)
        # 条式花格：下半一根中梃把窗身分成两扇，窗头里一个圆窗，圆窗里嵌四叶饰
        ocul = disc(306, deg, 30)
        mull = affinity.rotate(box(-3.2, -180, 3.2, -120), deg, origin=(0, 0))
        bars = unary_union([mull, ocul.buffer(5.5).difference(ocul)]).intersection(light.buffer(-6))
        g: list[str] = []
        glaze(light, deg, "ab"[i % 2], 17, 7, g, keep=unary_union([medal.buffer(5), ocul.buffer(5.5), mull]))
        g.extend(f'<path class="bar" d="{d_of(q)}"/>' for q in polys(bars))
        g.append(f'<path class="bd" d="{d_of(ocul)}"/>')
        quatre = foil(306, deg, 4, 13.5, 12.5, turn=45).intersection(ocul.buffer(-2))
        g.extend(f'<path class="fd{rng.choice("1123")}" d="{d_of(q)}"/>' for q in quarries(quatre, deg, 9))
        g.append(f'<path class="bd" d="{d_of(medal.buffer(5).difference(medal))}"/>')
        g.append(f'<path class="fm" d="{d_of(medal)}"/>')
        tx, ty = polar(212, deg)
        body.append(f'<g class="lancet" data-i="{i}" data-x="{tx:.1f}" data-y="{ty:.1f}">{"".join(g)}</g>')
        lights.append(light)
        # 主窗尖上的六叶饰
        six = foil(436, deg, 6, 10, 14)
        glaze(six, deg, "d", 11, 3.5, body)
        lights.append(six)
        # 两个窗头之间的四叶饰
        quad = foil(388, deg + step / 2, 4, 21, 21, turn=45)
        glaze(quad, deg + step / 2, "c", 13, 5, body)
        lights.append(quad)
        # 外圈的三叶饰，一室两个
        for off in (step / 4, 3 * step / 4):
            tre = foil(457, deg + off, 3, 13, 12)
            glaze(tre, deg + off, "d", 10, 3.5, body)
            lights.append(tre)
    # 最外一圈小圆窗
    for k in range(48):
        pearl = disc(491, k * 7.5 + 3.75, 5.2)
        body.append(f'<path class="fm" d="{d_of(pearl)}"/>')
        lights.append(pearl)
    # 中心：八叶饰里的一朵玫瑰，花瓣从外到内一层压一层
    eye = foil(0, 0, 8, 30, 66, turn=22.5)
    lights.append(eye)
    rose: list[str] = [f'<path class="bd" d="{d_of(eye)}"/>']
    for ring_i, (count, dist, rad, turn) in enumerate([(8, 62, 31, 22.5), (8, 44, 27, 0), (5, 27, 21, 18), (5, 13, 14, 54), (3, 5, 8, 0)]):
        for k in range(count):
            petal = disc(dist, turn + k * 360 / count, rad).intersection(eye.buffer(-5))
            for p in polys(petal):
                rose.append(f'<path class="fe{ring_i % 3 + 1}" d="{d_of(p)}"/>')
    rose.append(f'<path class="fm" d="{d_of(disc(0, 0, 4.5))}"/>')
    body.append(f'<g class="eye">{"".join(rose)}</g>')

    stone = Point(0, 0).buffer(R, 180).difference(unary_union(lights))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-R - 5} {-R - 5} {2 * R + 10} {2 * R + 10}">'
           f'<path class="stone" fill-rule="evenodd" d="{"".join(d_of(p) for p in polys(stone))}"/>'
           + "".join(body) + "</svg>\n")
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT.name}: {len(svg) // 1024} KB, {svg.count(chr(60) + chr(112) + chr(97))} paths")


if __name__ == "__main__":
    main()
