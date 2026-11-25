# 维护手册

这份文档写给维护这座馆的人。访客请看仓库首页的 README。文中的路径都相对仓库根目录。

把收藏库里的注意力模块办成一座博物馆的静态网站。主线是常设展「注意力简史」导览，馆长按年代分室讲注意力的历史，每室挑几件代表展品，以论文里的模块图为主。展品、时间线、关系图和统计四页供查阅。关系图有两种看法：平面的总图和 3D 的星团。谱系页在 2026-11-25 撤下，关系数据还在，展签上的「前作和后作」照常显示。网站支持中英文和深浅色，全部文件都在 `site/`，运行时不请求任何外部域名。

## 日常维护

收集队列每加一批模块，在本目录运行：

```powershell
python check.py
```

它先重新生成 `site/data/museum.json` 和 `site/data/code.json`，再核对数据和页面。全部通过时退出码为 0。退出码为 2 表示检查期间收集会话改了 INDEX 或队列文件，重跑一次即可。检查项包括：

- 队列每行恰好归入一件展品，INDEX 的注意力模块没有漏收。
- 谱系和关系图的边没有悬空，导览点名的代表展品都在馆内。
- 只展示照论文复现的代码，页面不从外部域名加载资源。
- museum.json 引用的论文图文件都在 `site/figures/`。
- 中英文案的键一致，英文模式显示的文案和数据字段里没有中日韩字符。失败时列出展品编号和字段名。

本机预览：

```powershell
python -m http.server 8780 -d site
```

然后打开 <http://localhost:8780>。网址加 `?lang=en` 或 `?theme=dark` 可以直接打开英文版或深色版。

## 原型

在项目根目录运行 `python -m http.server 8781`。原型从本机生成的 `museum.json` 读数据。功能取舍见[借鉴报告](docs/借鉴-2026-11-25.md)。

- [论文之间的引用](prototypes/citations/README.md)。打开 <http://localhost:8781/prototypes/citations/>。用 `python fetch_paper_metadata.py citations` 更新 OpenAlex 的馆内引用，再运行 `python check.py`。
- [两件展品对比](prototypes/compare/README.md)。打开 <http://localhost:8781/prototypes/compare/>。链接记住左右选择和筛选状态。
- [论文日期](prototypes/paper-dates/README.md)。打开 <http://localhost:8781/prototypes/paper-dates/>。用 `python fetch_paper_metadata.py dates` 更新 arXiv 首次提交日，再运行 `python check.py`。
- [注意力掩码](prototypes/mask/README.md)。打开 <http://localhost:8781/prototypes/mask/>。切换可见范围，观察同一组分数怎样得到不同权重。
- [放大论文图](prototypes/figure-viewer/README.md)。打开 <http://localhost:8781/prototypes/figure-viewer/>。支持放大、平移和复位。

## 数据来源

| 来源 | 取什么 |
|---|---|
| `INDEX.md` 模块总表 | 中文名、英文简称、出处、模块类型、应用领域、目录、来源备注 |
| 各模块目录的 `README.md` | 论文题目、作者、arXiv 或 DOI、官方仓库、固定提交、许可证、核对结论 |
| 各模块目录 `.py` 文件头 | AI缝合术批次的论文链接和官方仓库 |
| `工具与模板/模块收集/队列.md` | 状态、段、年份和出处、仓库、许可证、一句话机制（备注列） |
| `工具与模板/模块收集/队列-论文复现.md` | 照论文复现条目的状态和验证结果 |
| `工具与模板/模块收集/验证记录.md` | 照论文复现模块的核对结论 |
| `工具与模板/模块收集/扩队列记录.md` | 方向 a–k 的名称、每轮的序号范围、待扫方向 |

收录范围：`INDEX.md` 模块类型含「注意力」的条目，加上收集队列点名的目录。同一篇论文、同一模块名的多份代码并成一件展品，每份算一个馆藏副本。队列里没收进来的条目按「待入藏」「复现候选」「跳过」展出。

## 馆长手写层

`curation/` 放馆长手写的内容，和来源文件生成的数据分开。`build_data.py` 合并它们。文件不存在或写到一半读不成 JSON 时，脚本照常生成，只是少了对应内容。

| 文件 | 内容 | 怎么用 |
|---|---|---|
| `texts.part*.json` | `{展品编号: {mechanism_zh, mechanism_en, check_en, basis}}` | `mechanism_zh` 非空时替换队列备注里的简介，来源记为「馆长依据摘要撰写」。英文模式的简介和测试结果用 `mechanism_en`、`check_en` |
| `figures.json` | `{展品编号: {file, fig_no, caption, source_url, license}}`，图片在 `site/figures/` | 展品卡片和展签以这张图为主，图下写论文图编号和原文链接 |
| `story.json` | 导览稿：`thesis_zh/en` 和各展室的标题、年份、导语、正文、代表展品 | 序厅和 `#/tour` 页。稿子里的 `{n}` 换成展品总数 |
| `story_rooms/` | 导览的定稿：`00-thesis.json` 是开场白，其余一室一个文件。每室的 `sections` 是一段展墙文字加它讲到的展品 | 有这个目录时用它，没有时退回 `story.json` |

没有论文图的展品只写模块名，上面放一枚公版小花饰。

## 论文图的许可证

论文图的版权归原作者。每张图在 museum.json 里带 `license` 字段，取自 arXiv 的论文许可。线上站点和开源仓库对这些图的处理不同：

- **线上站点**放全部论文图，当作介绍论文时的引用。每张图写明是论文的第几张图，链接到原文，图下注明版权归原作者。图的长边压到 1000 像素。关于页写了撤图的办法，联系方式填在 `curation/site.json` 的 `contact` 里，可以是邮箱或网址。
- **开源仓库**同样带全部论文图，做法和线上站点一样（馆主 2026-11-25 定）。只想带作者允许再分发的图时，导出时加 `--cc-only`：它只带 CC BY、CC BY-SA、CC BY-NC-SA 和 CC0 的图，其余的由使用者运行 `python fetch_figures.py` 从 arXiv 取。

导出公开仓库的副本：

```powershell
python export_repo.py
```

它把 git 里的文件复制到 `dist/repo/`，去掉派工的工单、原型和只供馆长参考的调研，并查导出的文件里有没有本机路径。退出码为 0 才能公开。它只在本机生成文件，不推送。公开仓库是 <https://github.com/oscar030406/museum-of-attention>，`dist/repo/` 就是它的工作区：导出后在里面 `git add -A`、提交、推送。

没有图的展品在页面上画占位图，见上一节。

## 英文模式

英文模式只显示展品的英文名和各条记录 `en` 子表里的文字：

- 取值有限的字段（发表地点、类型、用途、Guo 综述的分类、年份依据、许可证、测试结果的出处）由 `build_data.py` 里的对照表译成英文。表里没有的新取值，build 时打印出来，英文模式不显示，补进对照表即可。
- 作者名里的「、」换成逗号，「和」换成 and，带中文的括注去掉。
- 只有中文原文的自由文本（收集备注、没收的原因、库内目录、中文论文题目），英文模式不显示那一行。
- 来源文件里本来就空的字段，两种语言都显示「缺」。

## 规则

- 来源文件里没有的字段，页面显示「缺」，脚本不补写。公式一栏，库里的 README 都没写，所以全部缺，展签上不列这一行，统计页照样计数。
- 代码来源分五类：作者的代码（作者或官方框架仓库的固定提交）、官方移植版（同上，README 写明换了框架）、照论文复现、转载（AI缝合术等合集）、来源不明。
- 方向 a–k 按 `扩队列记录.md` 里每个方向的条数，依次对应该轮的序号范围。条数和范围对不上时，那一轮不分配方向。
- 谱系只连三种能确定的关系：名称带版本号且前一版在馆、论文题目点名另一件展品、队列备注同一句话写明「替换、改进、扩展、基于」。普通英文词组成的名字（`TITLE_STOP`）、同缩写撞名、同一篇论文的两个模块不连。A→B→C 已连通时不画 A→C。
- 关系图的节点是展品，以及它们共有的展厅、扫描方向、出处、仓库和年份。仓库只给至少两件展品共用的建节点。边只用已有字段，不推断新关系。
- 网站只展示照论文复现的代码，这些是自己写的。其他来源只放元数据和链接，因为约 40 个仓库没有明确许可证。

## 第三方组件

图谱库和字体由 `vendor-build/` 打包进 `site/assets/`，版本锁在 `vendor-build/package.json`：3d-force-graph 1.80.2、three.js 0.187.0（MIT），Archivo、IBM Plex Mono（SIL OFL 1.1，许可证在 `site/assets/fonts/`）。升级时运行：

```powershell
cd vendor-build; npm ci; npm run build
```

然后改关于页里的版本号，`check.py` 会核对两处是否一致。

论文图原型使用 OpenSeadragon 5.0.1（BSD-3-Clause）。许可证随模块打包到 `site/assets/vendor/LICENSE-OpenSeadragon.txt`。接入正式页面时，把组件信息加入关于页。

## 部署

网站是纯静态文件，只上传 `site/` 目录的内容。上传前用默认模式生成数据（`python check.py`），这样站点带全部论文图。页面路由用 `#` 号，服务器不需要改写规则。线上站点在 <https://attention.chenmingkun.cn>，用的配置是 `deploy/nginx.attention.conf`。更新线上站点时，把 `site/` 打成压缩包传到服务器，解到站点根目录。`deploy/nginx.conf.example` 是通用的 nginx 配置样例，开了 gzip 压缩，并让数据文件每次向服务器确认更新。

## 许可

- 代码按 MIT 许可开放，见 `LICENSE`。
- 导览稿（`curation/story_rooms/`）、简介（`curation/texts.part*.json`）和关于页的文字按 CC BY 4.0 开放，见 `LICENSE-CONTENT.md`。
- 论文图不在这两份许可里，版权归各自的作者。每张图的许可写在 `curation/figures.json`。
- 第三方组件和公版纹样各按自己的许可，见「第三方组件」和 `site/assets/ornaments/README.md`。

## 文件

```
build_data.py         生成数据，--public 只带能再分发的论文图
check.py              生成数据并跑全部检查
export_repo.py        导出可以公开的仓库副本到 dist/repo/
fetch_figures.py      从 arXiv 取论文图
curation/             馆长手写层：简介、论文图清单、导览稿、撤图的联系方式
site/figures/         论文图
site/index.html       页面
site/assets/          样式、脚本（app.js 主体，graph.js 关系图）、馆徽
site/assets/vendor/   打包的图谱库，不要手改
site/assets/fonts/    站内字体和许可证，不要手改
site/data/            生成的数据，不要手改
vendor-build/         打包第三方组件的脚本和锁定的版本
deploy/               服务器配置样例
```

生成关系：`INDEX.md`、模块 README、队列文件、`curation/*.json` → `site/data/*.json` → `python check.py`。`vendor-build/package.json` → `site/assets/vendor/`、`site/assets/fonts/` → `npm run build`。

首页的玫瑰窗由 `make_rose.py` 用几何运算生成：`make_rose.py` → `site/assets/rose.svg` → `uv run make_rose.py`。玻璃的颜色不在这个文件里，在 `site/assets/style.css` 的两套主题变量里。

画框的镶嵌边带和馆徽同样由脚本生成：`make_ornaments.py` → `site/assets/frame-light.svg`、`site/assets/frame-dark.svg`、`site/assets/emblem.svg`、`site/index.html` 里的 `<symbol id="emblem">` → `uv run make_ornaments.py`。两套颜色写在脚本顶部的 `PALETTES` 里。馆徽是一张 4×4 的因果注意力权重图：下三角按权重着色，上三角是被掩码挡住的空格子。

## 视觉

浅色主题是经典哥特：石墙底色、宝石红、群青、赭石。深色主题是暗色哥特：午夜蓝黑、蓝紫、银线。装饰只用平涂色块和线条，不用渐变仿材质。画框分两种：展室里一页挂很多幅，用细线加公版角花。展签只挂一幅，用两道细线。生成的镶嵌边带（`frame-*.svg`）在 2026-11-25 撤下，文件留着没用。公版纹样的出处在 `site/assets/ornaments/README.md`。颜色变量集中在 `site/assets/style.css` 末尾的「两套哥特」和「玫瑰窗」两节。

这个文件是分几次追加写成的，后面的规则盖住前面的，改样式时从文件末尾往前找。
