/* 注意力博物馆 · 前端
   数据只来自 data/museum.json（由 build_data.py 生成）。取不到的字段显示「缺」。
   英文模式只显示 name_en 和各对象 en 子表里的文字。只有中文原文、没有英文版的字段，英文模式不显示那一行。 */
"use strict";

// ------------------------------------------------------------------ 文案
const I18N = {
  zh: {
    skip: "跳到正文", loading: "正在开馆……", loadFail: "没读到数据。在本目录运行 python build_data.py，再用 python -m http.server 打开 site/ 目录。",
    "nav.tour": "导览", "nav.timeline": "时间线", "nav.gallery": "展品", "nav.lineage": "谱系", "nav.census": "统计", "nav.about": "关于",
    navLabel: "主导航", langLabel: "Switch to English", themeLabel: "切换深浅色", brand: "注意力博物馆", brandSub: "Museum of Attention",
    theme_auto: "自动", theme_light: "浅色", theme_dark: "深色",
    foyerTitle: "注意力<br>博物馆",
    curator1: (n, y0, y1) => `这里收着 ${y0} 到 ${y1} 年的 ${n} 个注意力模块，都是能运行的代码。`,
    curator2: "每张展签写着论文出处、代码来源和测试结果。写着「缺」的一栏，库里没有记录。藏品还在增加。",
    curatorSig: "馆长",
    startTour: "从第一室看起", toGallery: "看全部展品", randomOne: "随便看一件",
    fCollected: "已收藏", fPending: "待收", fSpan: "年代", fEdges: "谱系连线",
    roomsTitle: "注意力简史", roomsLede: n => `常设展，共 ${n} 个展室，按年代走。`,
    roomsNone: "导览稿还在写。先去展品页看看。",
    room: n => `第 ${n} 室`, roomOf: (i, n) => `第 ${i} 室，共 ${n} 室`,
    prevRoom: "上一室", nextRoom: "下一室", backTour: "导览目录", roomAll: n => `这一时期的全部展品（${n} 件）`,
    roomObjects: "这一室的展品", openLabel: "看展签",
    earliestTitle: "最早的几件", earliestLede: "按论文年份排在最前面的藏品。",
    amapTitle: "各领域每年收了多少", amapLede: "行是展厅，列是论文年份。格子越深，那一年收的越多。点格子看那几件。",
    amapLegend: "每格件数", unknownYear: "年份不详", total: "合计",
    tlTitle: "时间线", tlLede: (a, b) => `${a} 到 ${b} 年，每年出了哪些注意力模块。实线框是已收藏的，虚线框是还没收的。左边细线的颜色是代码来源。`,
    tlCount: n => `${n} 件`, showPending: "也显示还没收的", jumpYear: "跳到年份",
    galTitle: "展厅", allHalls: "全部展品", byField: "按领域", byDirection: "按收集方向", unscanned: "还没收",
    search: "搜名字或论文题目", yearFrom: "年份从", yearTo: "到", sort: "排序",
    sortYearAsc: "从早到晚", sortYearDesc: "从晚到早", sortName: "按名字",
    results: n => `${n} 件`, showMore: "再看 60 件", noResult: "没找到。换个词，或者少选几个条件。",
    reset: "清空条件", hallsBtn: "选展厅",
    hallDirLede: "这一组是扩充收集时按这个方向找来的。",
    lineageTitle: "谱系", lineageLede: "谁改自谁。线只连三种有据可查的关系：名字里带版本号，论文题目提到前作，收集备注里写明了改自谁。横轴是论文年份，一个家族占一条横带。",
    famListTitle: "各家族和依据", fam: n => `家族 ${n}`, families: n => `${n} 个家族`, objectsN: n => `${n} 件展品`,
    ruleLabel: { "名称版本号": "名字里带版本号", "题目点名": "论文题目提到它", "备注写明": "收集备注写明" },
    lineageNone: "还没有能连上的。",
    censusTitle: "统计", censusLede: "这一页是账本：收了多少，还差多少，哪些地方没有记录。",
    cDirTitle: "按收集方向", cDirLede: "扩充馆藏的时候，我按 11 个方向去找论文。每个方向找到多少、收进来多少，都在这里。",
    cFieldTitle: "按领域", cFieldLede: "按领域数。还没收进来的，按它将来要放的领域算。",
    cSegTitle: "分段收集", cSegLede: "收集是分几段做的。每一段收了多少、还剩多少。",
    cMissTitle: "展签上空着的项", cMissLede: n => `已收藏的 ${n} 件里，每一项有多少件没有记录。库里的 README 都没写公式，所以公式一项全空。`,
    cSkipTitle: n => `没收的 ${n} 条和原因`, cNoCodeTitle: n => `找不到官方代码的 ${n} 条`,
    direction: "方向", collected: "已收藏", pending: "待收", candidate: "打算复现", skipped: "没收", bar: "比例", segment: "段", repro: "照论文复现",
    statusName: { collected: "已收藏", pending: "待收", candidate: "打算复现", skipped: "没收" },
    qStatus: { "已收": "已收", "待收": "待收", "跳过": "没收", "已复现": "已复现", "待复现": "待复现", "候选": "候选" },
    qSeg: { "复现": "复现" },
    field: "项", count: "件数",
    missName: { name_zh: "中文名", title: "论文题目", year: "年份", venue: "发表在", mechanism: "简介", formula: "公式", license: "许可证", verification: "测试结果", repo: "代码仓库", paper_link: "论文链接" },
    srcName: { author: "作者的代码", port: "官方移植版", repro: "照论文复现", third: "转载", unknown: "来源不明" },
    srcHint: { author: "取自作者或官方框架的仓库，固定在某一版", port: "官方代码，README 写明换了框架", repro: "没有官方代码，照论文自己写的", third: "从 AI缝合术等合集转来，没有逐行核对", unknown: "记录里没写代码从哪来" },
    miss: "缺", missTip: "库里没有这一项的记录",
    paper: "论文", noRepo: "无", close: "关闭",
    figNo: f => { const m = /(\d+)/.exec(f.fig_no || ""); return m ? `论文图 ${m[1]}` : "论文图"; },
    figSrc: "原文", noFig: "还没配上论文图", figLic: "图的许可",
    figLicName: { arxiv: "arXiv 默认许可", cc: s => `知识共享 ${s}`, other: s => s },
    mechBy: { "馆长依据摘要撰写": "馆长根据论文摘要写", "队列备注": "摘自收集备注" },
    inTour: "在导览里", backRoom: n => `回到第 ${n} 室`,
    relTitle: "前作和后作", parents: "它改自", children: "后来改自它的",
    recTitle: "档案",
    tYear: "年份", tVenue: "发表在", tAuthors: "作者", tPaper: "论文", tRepo: "代码仓库", tLicense: "许可证", tSource: "代码来源", tVerify: "测试结果", tMech: "简介", tHall: "展厅", tDirection: "收集方向", tType: "类型", tDomain: "用途", tGuo: "Guo 综述的分类", tStatus: "状态", tId: "馆藏号",
    yearFrom_: s => `依据：${s}`,
    copiesTitle: n => `库里的代码（${n} 份）`, commit: "代码版本", srcFile: "源文件", verifyFrom: s => `出自 ${s}`,
    queueTitle: "收集记录", queueMain: "队列", queueRepro: "论文复现队列", queueNo: (q, n) => `${q}第 ${n} 条`,
    codeTitle: "代码", codeRepro: "照论文复现的代码是自己写的，可以直接看。", codeNone: "别处来的代码留在库里，这里只放链接。",
    skipReason: "没收的原因", plannedSrc: "打算从哪收", licRepro: "不适用，代码是照论文自己写的",
    aboutTitle: "关于",
    footer: (g, n) => `数据更新于 ${g} · ${n} 条记录 · 个人收藏，不作商业用途`,
  },
  en: {
    skip: "Skip to content", loading: "Opening…", loadFail: "The data did not load. Run python build_data.py in this folder, then serve site/ with python -m http.server.",
    "nav.tour": "Tour", "nav.timeline": "Timeline", "nav.gallery": "Objects", "nav.lineage": "Lineage", "nav.census": "Numbers", "nav.about": "About",
    navLabel: "Main", langLabel: "Switch to Chinese", themeLabel: "Switch light or dark", brand: "Museum of Attention", brandSub: "",
    theme_auto: "Auto", theme_light: "Light", theme_dark: "Dark",
    foyerTitle: "Museum<br>of Attention",
    curator1: (n, y0, y1) => `${n} attention modules from ${y0} to ${y1}, all of them working code.`,
    curator2: "Each label gives the paper, where the code came from and how it held up in testing. A field marked “not recorded” is empty in the library too. The collection keeps growing.",
    curatorSig: "The curator",
    startTour: "Start in Room 1", toGallery: "Browse all objects", randomOne: "Show me one",
    fCollected: "In the collection", fPending: "Still to collect", fSpan: "Years", fEdges: "Lineage links",
    roomsTitle: "A short history of attention", roomsLede: n => `The permanent exhibition: ${n} rooms, in order of time.`,
    roomsNone: "The tour is still being written. The objects page is open in the meantime.",
    room: n => `Room ${n}`, roomOf: (i, n) => `Room ${i} of ${n}`,
    prevRoom: "Previous room", nextRoom: "Next room", backTour: "All rooms", roomAll: n => `Everything from these years (${n})`,
    roomObjects: "In this room", openLabel: "Open label",
    earliestTitle: "The oldest pieces", earliestLede: "The objects with the earliest paper years.",
    amapTitle: "What came in, by field and year", amapLede: "Rows are galleries, columns are paper years. Darker cells hold more objects. Click a cell to see them.",
    amapLegend: "Objects per cell", unknownYear: "Year unknown", total: "Total",
    tlTitle: "Timeline", tlLede: (a, b) => `Attention modules by paper year, ${a} to ${b}. Solid frames are in the collection. Dashed frames are still to collect. The thin line on the left shows where the code came from.`,
    tlCount: n => `${n}`, showPending: "Include ones still to collect", jumpYear: "Jump to year",
    galTitle: "Galleries", allHalls: "All objects", byField: "By field", byDirection: "By collecting theme", unscanned: "not started",
    search: "Search names or paper titles", yearFrom: "From", yearTo: "to", sort: "Sort",
    sortYearAsc: "Oldest first", sortYearDesc: "Newest first", sortName: "By name",
    results: n => `${n} objects`, showMore: "Show 60 more", noResult: "Nothing matches. Try another word or fewer filters.",
    reset: "Clear filters", hallsBtn: "Galleries",
    hallDirLede: "These came in during a collecting round that searched this theme.",
    lineageTitle: "Lineage", lineageLede: "Who built on whom. A line appears only with written evidence: a version number in the name, a paper title that names the earlier work, or a collecting note that says so. Left to right is paper year. Each family has its own band.",
    famListTitle: "Families and evidence", fam: n => `Family ${n}`, families: n => `${n} families`, objectsN: n => `${n} objects`,
    ruleLabel: { "名称版本号": "Version number in the name", "题目点名": "Named in the paper title", "备注写明": "Stated in a collecting note" },
    lineageNone: "No links yet.",
    censusTitle: "The collection in numbers", censusLede: "This page is the ledger: what is held, what is still missing, and where the records have gaps.",
    cDirTitle: "By collecting theme", cDirLede: "When the collection was extended, I searched in eleven directions. Here is how much each one turned up and how much of it is now held.",
    cFieldTitle: "By field", cFieldLede: "Counted by field. Items not yet held are counted under the field they will go to.",
    cSegTitle: "Collecting queues", cSegLede: "Collecting was done in stages. This shows what each stage brought in and what it left.",
    cMissTitle: "Blank fields on the labels", cMissLede: n => `Out of ${n} objects in the collection, how many have no record for each field. No README in the library writes out a formula, so that field is blank everywhere.`,
    cSkipTitle: n => `${n} entries passed over`, cNoCodeTitle: n => `${n} entries with no official code`,
    direction: "Theme", collected: "In", pending: "To collect", candidate: "To rewrite", skipped: "Passed over", bar: "Share", segment: "Segment", repro: "Rewritten from paper",
    statusName: { collected: "In the collection", pending: "Still to collect", candidate: "To rewrite from paper", skipped: "Passed over" },
    qStatus: { "已收": "Collected", "待收": "To collect", "跳过": "Passed over", "已复现": "Rewritten", "待复现": "To rewrite", "候选": "Candidate" },
    qSeg: { "复现": "rewrite" },
    field: "Field", count: "Objects",
    missName: { name_zh: "Chinese name", title: "Paper title", year: "Year", venue: "Published in", mechanism: "Overview", formula: "Formula", license: "License", verification: "Test result", repo: "Code repository", paper_link: "Paper link" },
    srcName: { author: "Authors' code", port: "Official port", repro: "Rewritten from paper", third: "Reposted", unknown: "Unknown source" },
    srcHint: { author: "From the authors' or the official framework's repository, at a fixed commit", port: "Official code moved to another framework, as the README says", repro: "No official code exists, so this was written from the paper", third: "Copied from third-party module collections and not checked line by line", unknown: "The records do not say where the code came from" },
    miss: "not recorded", missTip: "The library has no record of this",
    paper: "Paper", noRepo: "none", close: "Close",
    figNo: f => f.fig_no || "Paper figure",
    figSrc: "Source", noFig: "No paper figure yet", figLic: "Figure license",
    figLicName: { arxiv: "arXiv non-exclusive license", cc: s => `Creative Commons ${s}`, other: s => s },
    mechBy: { "馆长依据摘要撰写": "Written by the curator from the abstract", "队列备注": "From the collecting notes" },
    inTour: "On the tour", backRoom: n => `Back to Room ${n}`,
    relTitle: "Before and after", parents: "Built on", children: "Later built on it",
    recTitle: "Record",
    tYear: "Year", tVenue: "Published in", tAuthors: "Authors", tPaper: "Paper", tRepo: "Code repository", tLicense: "License", tSource: "Code source", tVerify: "Test result", tMech: "Overview", tHall: "Gallery", tDirection: "Collecting theme", tType: "Type", tDomain: "Used for", tGuo: "Type in the Guo et al. survey", tStatus: "Status", tId: "ID",
    yearFrom_: s => `from ${s}`,
    copiesTitle: n => `Code in the library (${n})`, commit: "Commit", srcFile: "Source file", verifyFrom: s => `from ${s}`,
    queueTitle: "Collecting record", queueMain: "Queue", queueRepro: "Rewrite queue", queueNo: (q, n) => `${q} #${n}`,
    codeTitle: "Code", codeRepro: "We wrote this code ourselves from the paper, so it is shown here.", codeNone: "Code from other sources stays in the library. This page links to it.",
    skipReason: "Why it was passed over", plannedSrc: "Planned source", licRepro: "Does not apply. We wrote the code from the paper.",
    aboutTitle: "About",
    footer: (g, n) => `Data updated ${g} · ${n} records · a personal, non-commercial collection`,
  },
};

// ------------------------------------------------------------------ 状态
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* 隐私窗口里写不了，忽略即可 */ } },
};
// 网址里的 ?lang=en、?theme=dark 优先，便于分享指定语言的链接和截图
const urlOpt = new URLSearchParams(location.search);
let lang = ["zh", "en"].includes(urlOpt.get("lang")) ? urlOpt.get("lang") : store.get("acm-lang") || ((navigator.language || "zh").toLowerCase().startsWith("zh") ? "zh" : "en");
if (["light", "dark"].includes(urlOpt.get("theme"))) document.documentElement.setAttribute("data-theme", urlOpt.get("theme"));
let D = null;          // museum.json
let byId = new Map();
let CODE = null;       // code.json，按需加载
let baseRoute = "";    // 打开展签抽屉时，底下那一页
const t = (k, ...a) => { const v = (I18N[lang][k] ?? I18N.zh[k]); return typeof v === "function" ? v(...a) : v; };
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);
const main = () => $("#main");
const EN = () => lang === "en";

// ------------------------------------------------------------------ 小部件
function miss() { return `<span class="miss" title="${esc(t("missTip"))}">${esc(t("miss"))}</span>`; }
// 取一个字段的显示文字。中文模式取原字段，英文模式取 o.en[enK]。
// 返回 null 表示「有中文原文、没有英文版」：调用方不显示这一行。字段本来就空时返回「缺」。
function fv(o, k, enK = k) {
  if (!EN()) return o[k] ? esc(o[k]) : miss();
  if (o.en && o.en[enK]) return esc(o.en[enK]);
  return o[k] ? null : miss();
}
function txt(o, k, enK = k) { return EN() ? (o.en && o.en[enK]) || null : o[k] || null; }
function zhName(e) { return EN() ? null : e.name_zh; }
function srcMark(e) {
  if (e.status !== "collected") return `<span class="src ${e.status}">${esc(t("statusName")[e.status])}</span>`;
  const k = e.source_type || "unknown";
  return `<span class="src ${k}" title="${esc(t("srcHint")[k])}">${esc(t("srcName")[k])}</span>`;
}
function paperUrl(e) {
  if (e.paper_url) return e.paper_url;
  if (e.arxiv) return `https://arxiv.org/abs/${e.arxiv}`;
  if (e.doi) return `https://doi.org/${e.doi}`;
  return null;
}
function repoUrl(o) { return o.repo_url || (o.repo && !o.repo.includes(":") ? `https://github.com/${o.repo}` : null); }
function hallName(field, task) {
  const f = EN() ? (D.field_en[field] || field) : field;
  if (!task) return f;
  return EN() ? (D.field_en[task] || task) : task;
}
function dirName(k) { const d = D.directions[k]; return d ? `${k}. ${EN() ? (d.en || k) : d.zh}` : k; }
function hallKey(h) { return h.task ? `t:${h.field}/${h.task}` : `f:${h.field}`; }
function out(href, label) { return `<a class="out" href="${esc(href)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`; }
function evidence(g) { return EN() ? g.evidence_en : g.evidence; }
function paras(s) { return String(s || "").split(/\n\s*\n/).map(p => p.trim()).filter(Boolean).map(p => `<p>${esc(p)}</p>`).join(""); }
// 导览稿的 *_zh / *_en。稿子里的 {n} 是展品总数，随数据更新，不写死
function sx(o, k) { return o ? String((EN() ? o[k + "_en"] : o[k + "_zh"]) || "").replaceAll("{n}", D.exhibits.length) : ""; }

const tip = {
  el: null,
  show(html, x, y) {
    const el = this.el || (this.el = $("#tip"));
    el.innerHTML = html; el.hidden = false;
    const r = el.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > innerHeight - 8) top = y - r.height - 14;
    el.style.left = Math.max(8, left) + "px"; el.style.top = Math.max(8, top) + "px";
  },
  hide() { if (this.el) this.el.hidden = true; },
};

// ------------------------------------------------------------------ 论文图
// 没有图或图没加载出来时，只写模块名，上面的小花饰由样式表加。
function placeholder(e) {
  return `<span class="ph-name" lang="en">${esc(e.name_en)}</span><span class="ph-note">${esc(t("noFig"))}</span>`;
}
function figBox(e, cls = "", eager = false) {
  const f = e.figure;
  if (!f) return `<div class="fig fig-ph ${cls}" data-id="${esc(e.id)}">${placeholder(e)}</div>`;
  const alt = `${e.name_en} · ${t("figNo", f)}`;
  return `<div class="fig ${cls}" data-id="${esc(e.id)}"><img src="${esc(f.file)}" alt="${esc(alt)}" loading="${eager ? "eager" : "lazy"}" decoding="async" onerror="figFail(this)"></div>`;
}
window.figFail = img => {
  const box = img.closest(".fig"); const e = box && byId.get(box.dataset.id);
  if (!e) return;
  box.classList.add("fig-ph"); box.innerHTML = placeholder(e);
  const cap = box.parentElement && box.parentElement.querySelector(".fig-cap"); if (cap) cap.remove();
};
function figLicense(lic) {
  if (!lic) return null;
  const names = t("figLicName");
  if (/arxiv\.org\/licenses\/nonexclusive/i.test(lic)) return names.arxiv;
  const m = /creativecommons\.org\/(?:licenses|publicdomain)\/([a-z-]+)\/([\d.]+)/i.exec(lic);
  if (m) return names.cc(m[1] === "zero" ? `CC0 ${m[2]}` : `CC ${m[1].toUpperCase()} ${m[2]}`);
  return names.other(lic);
}
function figCap(e, withLink = true) {
  const f = e.figure; if (!f) return "";
  const href = f.source_url || paperUrl(e);
  return `<div class="fig-cap"><span class="fig-no">${esc(t("figNo", f))}</span>${withLink && href ? out(href, t("figSrc")) : ""}</div>`;
}

// 简介：英文模式只显示英文版。只有中文版时返回空串，字段本来就空时返回「缺」。
function mechHtml(e) {
  if (!e.mechanism) return `<span class="muted">${esc(t("tMech"))}</span> ${miss()}`;
  return fv(e, "mechanism") || "";
}

// ------------------------------------------------------------------ 展签卡片
function labelCard(e) {
  const zh = zhName(e) ? `<small>${esc(e.name_zh)}</small>` : "";
  const year = e.year ? `<span class="label-year">${e.year}</span>` : `<span class="label-year none">${esc(t("unknownYear"))}</span>`;
  const venue = txt(e, "venue");
  const lic = e.status === "collected" && e.source_type !== "repro" && e.license ? `<span>${esc(EN() ? (e.en.license || "") : e.license)}</span>` : "";
  return `<article class="label ${e.status}">
    ${figBox(e)}
    ${figCap(e)}
    <div class="label-body">
      <div class="label-top">${year}<span class="label-venue">${venue ? esc(venue) : ""}</span></div>
      <h3 class="label-name"><a href="#/x/${encodeURIComponent(e.id)}">${esc(e.name_en)}</a>${zh}</h3>
      <p class="label-mech">${mechHtml(e)}</p>
      <div class="label-foot">${srcMark(e)}${lic}</div>
    </div>
  </article>`;
}

// ------------------------------------------------------------------ 序厅和导览
function chapters() { return (D.story && Array.isArray(D.story.chapters)) ? D.story.chapters : []; }
function roomYears(c) { const [a, b] = c.years || []; return a && b && a !== b ? `${a}–${b}` : `${a || b || ""}`; }
function roomList() {
  const cs = chapters();
  if (!cs.length) return `<p class="empty">${esc(t("roomsNone"))} <a href="#/gallery">${esc(t("toGallery"))} →</a></p>`;
  return `<ol class="rooms">${cs.map((c, i) => {
    const thumbs = (c.anchors || []).map(a => byId.get(a.id)).filter(e => e && e.figure).slice(0, 1);
    return `<li class="room-entry"><a href="#/tour/${encodeURIComponent(c.id)}">
      <div class="room-entry-text"><span class="room-no">${String(i + 1).padStart(2, "0")} · ${esc(roomYears(c))}</span>
        <h3>${esc(sx(c, "title"))}</h3><p>${esc(sx(c, "lede"))}</p></div>
      <div class="room-thumbs">${thumbs.map(e => figBox(e, "thumb")).join("")}</div></a></li>`;
  }).join("")}</ol>`;
}
// 首页的玫瑰窗：一片花瓣一个展室，从正上方起顺时针排。全部是平涂的色块和线，不仿材质。
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
function roseWindow() { return `<div class="rose2" id="rose-slot" role="group" aria-label="${EN() ? "Rose window of the rooms" : "展室的玫瑰窗"}"></div>`; }
// 玫瑰窗由 make_rose.py 生成（assets/rose.svg）。这里把它放进页面，再给八个主窗洞接上展室。
let ROSE_SVG = null;
async function mountRose(cs) {
  const slot = $("#rose-slot");
  if (!slot) return;
  try { if (!ROSE_SVG) ROSE_SVG = await (await fetch("assets/rose.svg")).text(); } catch (err) { return; }
  if (!document.body.contains(slot)) return;
  slot.innerHTML = ROSE_SVG;
  slot.querySelectorAll("g.lancet").forEach(g => {
    const i = +g.dataset.i, c = cs[i];
    if (!c) return;
    const go = () => { location.hash = `#/tour/${encodeURIComponent(c.id)}`; };
    g.setAttribute("role", "link"); g.setAttribute("tabindex", "0");
    g.setAttribute("aria-label", `${t("room", i + 1)} ${sx(c, "title")}`);
    g.insertAdjacentHTML("beforeend", `<title>${esc(sx(c, "title"))} · ${esc(roomYears(c))}</title><text class="rose-n" x="${g.dataset.x}" y="${g.dataset.y}">${ROMAN[i] || i + 1}</text>`);
    g.addEventListener("click", go);
    g.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); } });
  });
}
function renderFoyer() {
  // 首页只做两件事：馆长的开场白，和八个展室的入口。统计数字在「统计」页。
  const col = D.exhibits.filter(e => e.status === "collected");
  const years = col.map(e => e.year).filter(Boolean);
  const cs = chapters();
  const thesis = sx(D.story, "thesis");
  main().innerHTML = `
  <section class="foyer-hero">
    <h1 class="foyer-title">${t("foyerTitle")}</h1>
    <div class="curator">
      <div class="thesis">${thesis ? paras(thesis) : `<p>${esc(t("curator1", col.length, Math.min(...years), Math.max(...years)))}</p>`}</div>
      <p class="sig">${esc(t("curatorSig"))}</p>
      <div class="hero-actions">
        ${cs.length ? `<a class="btn" href="#/tour/${encodeURIComponent(cs[0].id)}">${esc(t("startTour"))}</a>` : ""}
        <a class="btn ${cs.length ? "ghost" : ""}" href="#/gallery">${esc(t("toGallery"))}</a>
        <button class="btn ghost" type="button" id="random-btn">${esc(t("randomOne"))}</button>
      </div>
    </div>
  </section>
  ${cs.length ? `<section class="section plan-sec">
    <h2 class="rooms-h">${EN() ? "The rose window" : "玫瑰窗"}</h2>
    <p class="plan-note">${EN() ? "Eight petals, eight rooms. Start with Room I at the top and go clockwise." : "八片花瓣是八个展室。从正上方的第 I 室起，顺时针走一圈。"}</p>
    <div class="plan-wrap">${roseWindow(cs)}<ol class="rose-legend">${cs.map((c, i) => `<li><a href="#/tour/${encodeURIComponent(c.id)}"><b>${ROMAN[i] || i + 1}</b><span>${esc(sx(c, "title"))}</span><small>${esc(roomYears(c))}</small></a></li>`).join("")}</ol></div>
  </section>` : ""}
  <section class="section">
    <h2 class="rooms-h">${esc(t("roomsTitle"))}</h2>
    ${roomList()}
  </section>`;
  mountRose(cs);
  $("#random-btn").addEventListener("click", () => { const e = col[Math.floor(Math.random() * col.length)]; location.hash = `#/x/${encodeURIComponent(e.id)}`; });
}
function renderTourIndex() {
  const cs = chapters();
  const thesis = sx(D.story, "thesis");
  main().innerHTML = `
  <header class="page-head"><h1>${esc(t("roomsTitle"))}</h1>${thesis ? `<div class="thesis">${paras(thesis)}</div>` : ""}${cs.length ? `<p>${esc(t("roomsLede", cs.length))}</p>` : ""}</header>
  ${roomList()}`;
}
function renderRoom(id) {
  const cs = chapters();
  const i = cs.findIndex(c => c.id === id);
  if (i < 0) return renderTourIndex();
  const c = cs[i];
  const more = c.more || {};
  const m0 = more.y0 ?? (c.years || [])[0], m1 = more.y1 ?? (c.years || [])[1];
  const nAll = D.exhibits.filter(e => e.status === "collected" && e.year && (!m0 || e.year >= m0) && (!m1 || e.year <= m1)).length;
  const qs = new URLSearchParams(); if (m0) qs.set("y0", m0); if (m1) qs.set("y1", m1); qs.set("st", "collected");
  // 一段展墙文字，旁边挂它讲到的展品。有论文图的挂图，没有的只留一条文字。
  const plate = a => {
    const e = byId.get(a.id);
    if (!e) return "";
    const href = `#/x/${encodeURIComponent(e.id)}`;
    return `<figure class="plate${e.figure ? "" : " plain"}">
      ${e.figure ? `<a class="plate-fig" href="${href}">${figBox(e, "big")}</a>` : ""}
      <figcaption>
        <span class="plate-year">${[e.year, txt(e, "venue")].filter(Boolean).map(esc).join(" · ")}</span>
        <h3><a href="${href}">${esc(e.name_en)}</a>${zhName(e) ? `<small>${esc(e.name_zh)}</small>` : ""}</h3>
        <p>${esc(sx(a, "note") || txt(e, "mechanism") || "")}</p>
        <span class="plate-acc">${EN() ? "Acc. no." : "馆藏号"} ${esc(e.id)}</span>
      </figcaption>
    </figure>`;
  };
  const sections = c.sections || [{ text_zh: c.body_zh, text_en: c.body_en, anchors: c.anchors || [] }];
  const walls = sections.map(s => `
    <section class="wall${(s.anchors || []).length ? "" : " alone"}">
      <div class="wall-text">${paras(sx(s, "text"))}</div>
      ${(s.anchors || []).length ? `<div class="wall-objects">${s.anchors.map(plate).join("")}</div>` : ""}
    </section>`).join("");
  const pager =(j, label, cls) => cs[j] ? `<a class="pager ${cls}" href="#/tour/${encodeURIComponent(cs[j].id)}"><small>${esc(label)} · ${esc(t("room", j + 1))}</small><b>${esc(sx(cs[j], "title"))}</b></a>` : `<span class="pager ${cls} none"></span>`;
  main().innerHTML = `
  <article class="room">
    <nav class="room-crumb"><a href="#/tour">${esc(t("backTour"))}</a><span>${esc(t("roomOf", i + 1, cs.length))}</span></nav>
    <header class="room-head">
      <span class="room-num" aria-hidden="true">${ROMAN[i] || i + 1}</span>
      <div class="room-years">${esc(t("room", i + 1))} · ${esc(roomYears(c))}</div>
      <h1>${esc(sx(c, "title"))}</h1>
      ${sx(c, "lede") ? `<p class="room-lede">${esc(sx(c, "lede"))}</p>` : ""}
    </header>
    ${walls}
    <div class="room-end" aria-hidden="true"></div>
    <p class="room-all"><a class="btn ghost" href="#/gallery?${qs}">${esc(t("roomAll", nAll))} →</a></p>
    <nav class="room-pager">${pager(i - 1, t("prevRoom"), "prev")}${pager(i + 1, t("nextRoom"), "next")}</nav>
  </article>`;
}

// ------------------------------------------------------------------ 时间线
function renderTimeline(params) {
  const showPend = params.get("pending") !== "0";
  const list = D.exhibits.filter(e => e.status === "collected" || (showPend && (e.status === "pending" || e.status === "candidate")));
  const years = [...new Set(list.map(e => e.year).filter(Boolean))].sort((a, b) => a - b);
  const groups = years.map(y => [y, list.filter(e => e.year === y)]);
  const unknown = list.filter(e => !e.year);
  if (unknown.length) groups.push(["na", unknown]);
  const maxN = Math.max(...groups.map(g => g[1].length));
  const order = { author: 0, port: 1, repro: 2, third: 3, unknown: 4 };
  const item = e => {
    const cls = e.status === "collected" ? (e.source_type || "unknown") : e.status;
    const sub = zhName(e) || txt(e, "venue") || (e.status !== "collected" ? t("statusName")[e.status] : "");
    const title = txt(e, "title") || "";
    return `<a class="tli ${cls}" href="#/x/${encodeURIComponent(e.id)}" title="${esc(title + (e.status !== "collected" ? " · " + t("statusName")[e.status] : ""))}"><b>${esc(e.name_en)}</b><small>${esc(sub)}</small></a>`;
  };
  main().innerHTML = `
  <header class="page-head"><h1>${esc(t("tlTitle"))}</h1><p>${esc(t("tlLede", years[0], years[years.length - 1]))}</p></header>
  <div class="tl-intro">
    <div class="legend">${["author", "port", "repro", "third", "unknown"].map(k => `<span class="src ${k}">${esc(t("srcName")[k])}</span>`).join("")}<span class="src pending">${esc(t("statusName").pending)}</span></div>
    <label class="field"><input type="checkbox" id="tl-pend" ${showPend ? "checked" : ""}> ${esc(t("showPending"))}</label>
  </div>
  <nav class="yearbar" aria-label="${esc(t("jumpYear"))}">${groups.map(([y, es]) => `<a href="#/timeline" data-jump="y-${y}" title="${es.length}"><i style="height:${Math.max(2, Math.round(34 * es.length / maxN))}px"></i>${y === "na" ? "?" : y}</a>`).join("")}</nav>
  <div class="tl">${groups.map(([y, es]) => `
    <section class="tl-year" id="y-${y}">
      <div class="tl-y"><b>${y === "na" ? "?" : y}</b><span>${esc(y === "na" ? t("unknownYear") + " · " : "")}${esc(t("tlCount", es.length))}</span></div>
      <div class="tl-items">${es.sort((a, b) => (a.status !== "collected") - (b.status !== "collected") || (order[a.source_type] ?? 9) - (order[b.source_type] ?? 9) || a.name_en.localeCompare(b.name_en)).map(item).join("")}</div>
    </section>`).join("")}</div>`;
  $(".yearbar").addEventListener("click", ev => {
    const a = ev.target.closest("a[data-jump]"); if (!a) return;
    ev.preventDefault(); document.getElementById(a.dataset.jump)?.scrollIntoView({ block: "start" });
  });
  $("#tl-pend").addEventListener("change", ev => { location.hash = ev.target.checked ? "#/timeline" : "#/timeline?pending=0"; });
}

// ------------------------------------------------------------------ 展厅
const PAGE = 60;
function matchHall(e, hall) {
  if (!hall) return true;
  if (hall.startsWith("d:")) return e.direction === hall.slice(2);
  if (hall.startsWith("f:")) return e.halls.some(h => h.field === hall.slice(2));
  if (hall.startsWith("t:")) { const [f, tk] = hall.slice(2).split("/"); return e.halls.some(h => h.field === f && h.task === tk); }
  return true;
}
function filterExhibits(p) {
  const q = (p.get("q") || "").trim().toLowerCase();
  const hall = p.get("hall") || "";
  const y0 = p.get("y0"), y1 = p.get("y1");
  const src = (p.get("src") || "").split(",").filter(Boolean);
  const st = (p.get("st") || "").split(",").filter(Boolean);
  let list = D.exhibits.filter(e => {
    if (!matchHall(e, hall)) return false;
    if (st.length && !st.includes(e.status)) return false;
    if (src.length && !(e.status === "collected" && src.includes(e.source_type || "unknown"))) return false;
    if (y0 === "na") { if (e.year) return false; }
    else {
      if (y0 && (!e.year || e.year < +y0)) return false;
      if (y1 && (!e.year || e.year > +y1)) return false;
    }
    if (q) {
      const hay = [e.name_en, e.name_zh, e.title, e.mechanism, e.en && e.en.mechanism, ...(e.copies || []).map(c => c.name_en)].join(" ").toLowerCase();
      if (!q.split(/\s+/).every(w => hay.includes(w))) return false;
    }
    return true;
  });
  const sort = p.get("sort") || "asc";
  const ny = e => e.year || 9999;
  if (sort === "asc") list.sort((a, b) => ny(a) - ny(b) || a.name_en.localeCompare(b.name_en));
  else if (sort === "desc") list.sort((a, b) => (b.year || 0) - (a.year || 0) || a.name_en.localeCompare(b.name_en));
  else list.sort((a, b) => a.name_en.localeCompare(b.name_en, "en", { sensitivity: "base" }));
  return list;
}
function galleryHash(p) { const s = p.toString(); return "#/gallery" + (s ? "?" + s : ""); }

function renderGallery(p) {
  const hall = p.get("hall") || "";
  const list = filterExhibits(p);
  const shown = Math.min(list.length, +(p.get("n") || PAGE));
  const allYears = [...new Set(D.exhibits.map(e => e.year).filter(Boolean))].sort((a, b) => a - b);
  const src = (p.get("src") || "").split(",").filter(Boolean);
  const st = (p.get("st") || "").split(",").filter(Boolean);
  const fieldCount = (f, tk) => D.exhibits.filter(e => e.halls.some(h => h.field === f && (tk === undefined || h.task === tk))).length;
  const link = (key, label, n, cls = "") => {
    const np = new URLSearchParams(p); if (key) np.set("hall", key); else np.delete("hall"); np.delete("n");
    return `<li class="${cls}"><a href="${galleryHash(np)}" ${hall === key ? 'aria-current="true"' : ""}><span>${esc(label)}</span><span class="n">${n}</span></a></li>`;
  };
  let rail = `<h3>${esc(t("galTitle"))}</h3><ul>${link("", t("allHalls"), D.exhibits.length)}</ul><h3>${esc(t("byField"))}</h3><ul>`;
  for (const f of D.halls.fields) {
    rail += link(`f:${f.field}`, hallName(f.field), fieldCount(f.field));
    for (const tk of f.tasks) rail += link(`t:${f.field}/${tk.task}`, hallName(f.field, tk.task), fieldCount(f.field, tk.task), "sub");
  }
  rail += `</ul><h3>${esc(t("byDirection"))}</h3><ul>`;
  for (const d of D.halls.directions) rail += link(`d:${d.key}`, dirName(d.key) + (d.scanned ? "" : ` · ${t("unscanned")}`), d.count, d.scanned ? "" : "off");
  rail += "</ul>";

  let headTitle = t("allHalls"), headLede = "";
  if (hall.startsWith("d:")) { headTitle = dirName(hall.slice(2)); headLede = t("hallDirLede"); }
  else if (hall.startsWith("f:")) headTitle = hallName(hall.slice(2));
  else if (hall.startsWith("t:")) { const [f, tk] = hall.slice(2).split("/"); headTitle = `${hallName(f)} · ${hallName(f, tk)}`; }

  const yOpt = (sel) => [`<option value="">—</option>`, ...allYears.map(y => `<option value="${y}" ${String(y) === sel ? "selected" : ""}>${y}</option>`)].join("");
  const srcChip = k => `<button class="chip-t" type="button" data-src="${k}" aria-pressed="${src.includes(k)}"><span class="src ${k}">${esc(t("srcName")[k])}</span></button>`;
  const stChip = k => `<button class="chip-t" type="button" data-st="${k}" aria-pressed="${st.includes(k)}"><span class="src ${k === "collected" ? "author" : k}">${esc(t("statusName")[k])}</span></button>`;

  main().innerHTML = `
  <div class="gallery">
    <aside class="rail" id="rail" aria-label="${esc(t("galTitle"))}">${rail}</aside>
    <div>
      <header class="hall-head"><h2>${esc(headTitle)}</h2>${headLede ? `<p>${esc(headLede)}</p>` : ""}</header>
      <div class="toolbar">
        <button class="btn ghost rail-toggle" type="button" id="rail-toggle">${esc(t("hallsBtn"))}</button>
        <label class="search"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.5"/></svg><input id="q" type="search" placeholder="${esc(t("search"))}" value="${esc(p.get("q") || "")}" aria-label="${esc(t("search"))}"></label>
        <label class="field">${esc(t("yearFrom"))}<select id="y0">${yOpt(p.get("y0") || "")}</select></label>
        <label class="field">${esc(t("yearTo"))}<select id="y1">${yOpt(p.get("y1") || "")}</select></label>
        <label class="field">${esc(t("sort"))}<select id="sort">
          <option value="asc" ${(p.get("sort") || "asc") === "asc" ? "selected" : ""}>${esc(t("sortYearAsc"))}</option>
          <option value="desc" ${p.get("sort") === "desc" ? "selected" : ""}>${esc(t("sortYearDesc"))}</option>
          <option value="name" ${p.get("sort") === "name" ? "selected" : ""}>${esc(t("sortName"))}</option></select></label>
      </div>
      <div class="chips" aria-label="${esc(t("tSource"))}">${["author", "port", "repro", "third", "unknown"].map(srcChip).join("")}</div>
      <div class="chips" aria-label="${esc(t("tStatus"))}">${["collected", "pending", "candidate", "skipped"].map(stChip).join("")}</div>
      <div class="result-line"><span><strong>${esc(t("results", list.length))}</strong></span>${p.toString() ? `<a href="#/gallery">${esc(t("reset"))}</a>` : ""}</div>
      ${list.length ? `<div class="labels">${list.slice(0, shown).map(labelCard).join("")}</div>` : `<p class="empty">${esc(t("noResult"))}</p>`}
      ${shown < list.length ? `<button class="btn ghost more" type="button" id="more">${esc(t("showMore"))}</button>` : ""}
    </div>
  </div>`;

  const setP = (k, v) => { const np = new URLSearchParams(p); if (v) np.set(k, v); else np.delete(k); np.delete("n"); location.hash = galleryHash(np); };
  let timer;
  $("#q").addEventListener("input", ev => { clearTimeout(timer); timer = setTimeout(() => setP("q", ev.target.value.trim()), 250); });
  $("#y0").addEventListener("change", ev => setP("y0", ev.target.value));
  $("#y1").addEventListener("change", ev => setP("y1", ev.target.value));
  $("#sort").addEventListener("change", ev => setP("sort", ev.target.value === "asc" ? "" : ev.target.value));
  const toggleList = (key, val) => {
    const cur = (p.get(key) || "").split(",").filter(Boolean);
    const next = cur.includes(val) ? cur.filter(x => x !== val) : [...cur, val];
    setP(key, next.join(","));
  };
  main().querySelectorAll("[data-src]").forEach(b => b.addEventListener("click", () => toggleList("src", b.dataset.src)));
  main().querySelectorAll("[data-st]").forEach(b => b.addEventListener("click", () => toggleList("st", b.dataset.st)));
  $("#more")?.addEventListener("click", () => { const np = new URLSearchParams(p); np.set("n", shown + PAGE); history.replaceState(null, "", galleryHash(np)); route(true); });
  $("#rail-toggle").addEventListener("click", () => $("#rail").classList.toggle("open"));
}

// ------------------------------------------------------------------ 统计
function rowsForMap() {
  const rows = [];
  for (const f of D.halls.fields) {
    if (f.tasks.length) for (const tk of f.tasks) rows.push({ field: f.field, task: tk.task });
    else rows.push({ field: f.field, task: null });
  }
  return rows;
}
function binOf(n) { return n === 0 ? 0 : n === 1 ? 1 : n <= 3 ? 2 : n <= 7 ? 3 : n <= 15 ? 4 : n <= 31 ? 5 : 6; }
const BIN_LABELS = ["0", "1", "2–3", "4–7", "8–15", "16–31", "32+"];
function amapHtml(col) {
  const years = col.map(e => e.year).filter(Boolean);
  const y0 = Math.min(...years), y1 = Math.max(...years);
  const yrs = []; for (let y = y0; y <= y1; y++) yrs.push(y);
  const cnt = new Map();
  for (const e of col) for (const h of e.halls.slice(0, 1)) {
    const k = `${h.field}|${h.task || ""}|${e.year || "na"}`; cnt.set(k, (cnt.get(k) || 0) + 1);
  }
  const label = r => hallName(r.field, r.task);
  const head = `<tr><th class="k"></th>${yrs.map(y => `<th scope="col">${String(y).slice(2)}</th>`).join("")}<th scope="col">?</th></tr>`;
  const body = rowsForMap().map(r => {
    const cells = [...yrs, "na"].map(y => {
      const n = cnt.get(`${r.field}|${r.task || ""}|${y}`) || 0;
      const hk = r.task ? `t:${r.field}/${r.task}` : `f:${r.field}`;
      const yq = y === "na" ? "y0=na" : `y0=${y}&y1=${y}`;
      return `<td><button class="cell b${binOf(n)}" data-n="${n}" data-hall="${esc(label(r))}" data-year="${y}" ${n ? `data-go="#/gallery?hall=${encodeURIComponent(hk)}&${yq}&st=collected"` : "tabindex=\"-1\" aria-hidden=\"true\""} aria-label="${esc(label(r))} ${y}: ${n}">${n || ""}</button></td>`;
    }).join("");
    return `<tr><th scope="row">${esc(label(r))}</th>${cells}</tr>`;
  }).join("");
  const foot = `<tr><td class="k"></td>${yrs.map(y => `<td>${col.filter(e => e.year === y).length}</td>`).join("")}<td>${col.filter(e => !e.year).length}</td></tr>`;
  return `<div class="amap-wrap">
      <table class="amap"><thead>${head}</thead><tbody>${body}</tbody><tfoot>${foot}</tfoot></table>
      <div class="legend"><span>${esc(t("amapLegend"))}</span><span class="ramp">${BIN_LABELS.map((l, i) => `<i class="cell b${i}" title="${l}"></i>`).join("")}</span><span>${BIN_LABELS[0]} → ${BIN_LABELS[6]}</span><span class="muted">· ${esc(t("total"))} ${col.length}</span></div>
    </div>`;
}
function wireAmap() {
  const wrap = $(".amap-wrap");
  wrap.addEventListener("click", ev => { const b = ev.target.closest(".cell[data-go]"); if (b) location.hash = b.dataset.go; });
  wrap.addEventListener("mousemove", ev => {
    const b = ev.target.closest(".cell[data-hall]");
    if (!b) return tip.hide();
    const y = b.dataset.year === "na" ? t("unknownYear") : b.dataset.year;
    tip.show(`<b>${esc(b.dataset.hall)}</b><br>${esc(y)} · ${b.dataset.n}`, ev.clientX, ev.clientY);
  });
  wrap.addEventListener("mouseleave", () => tip.hide());
}
function sbar(c, unscanned) {
  const keys = ["collected", "pending", "candidate", "skipped"];
  const tot = keys.reduce((s, k) => s + (c[k] || 0), 0);
  if (!tot) return `<div class="sbar ${unscanned ? "unscanned" : ""}" aria-hidden="true"></div>`;
  return `<div class="sbar" role="img" aria-label="${keys.map(k => `${t("statusName")[k]} ${c[k] || 0}`).join(", ")}">${keys.filter(k => c[k]).map(k => `<i class="k-${k}" style="flex:${c[k]}" title="${esc(t("statusName")[k])} ${c[k]}"></i>`).join("")}</div>`;
}
function renderCensus() {
  const C = D.census;
  const col = D.exhibits.filter(e => e.status === "collected");
  const legend = `<div class="legend">${["collected", "pending", "candidate", "skipped"].map((k, i) => `<span><span class="sw" style="background:var(${["--c1", "--c2", "--c3", "--c-other"][i]})"></span>${esc(t("statusName")[k])}</span>`).join("")}</div>`;
  const dirRows = C.directions.map(d => `<tr class="${d.scanned ? "" : "off"}"><td>${esc(dirName(d.key))} ${d.scanned ? "" : `<span class="tag-off">${esc(t("unscanned"))}</span>`}</td>
    <td class="num">${d.collected}</td><td class="num">${d.pending}</td><td class="num">${d.candidate}</td><td class="num">${d.skipped}</td><td>${sbar(d, !d.scanned)}</td></tr>`).join("");
  const fieldRows = Object.entries(C.fields).sort((a, b) => Object.values(b[1]).reduce((s, x) => s + x, 0) - Object.values(a[1]).reduce((s, x) => s + x, 0))
    .map(([f, c]) => `<tr><td>${esc(f === "未归属" ? (EN() ? "Unassigned" : f) : hallName(f))}</td><td class="num">${c.collected || 0}</td><td class="num">${c.pending || 0}</td><td class="num">${c.candidate || 0}</td><td class="num">${c.skipped || 0}</td><td>${sbar(c)}</td></tr>`).join("");
  const qs = k => t("qStatus")[k] || k;
  const stKeys = ["已收", "待收", "跳过"];
  const segRows = Object.entries(C.segments).map(([s, c]) => `<tr><td>${esc(s)}</td>${stKeys.map(k => `<td class="num">${c[k] || 0}</td>`).join("")}</tr>`).join("");
  const rKeys = ["已复现", "待复现", "候选", "跳过"];
  const missCount = {};
  for (const e of col) for (const m of e.missing) missCount[m] = (missCount[m] || 0) + 1;
  const missRows = Object.keys(I18N.zh.missName).map(k => `<tr><td>${esc(t("missName")[k])}</td><td class="num">${missCount[k] || 0}</td><td class="num">${((100 * (missCount[k] || 0)) / col.length).toFixed(0)}%</td></tr>`).join("");
  const reason = s => EN() ? "" : `<br>${esc(s.reason)}`;     // 原因只有中文原文，英文模式不显示
  const skip = C.skipped.map(s => `<li><b>${esc(s.name)}</b> <span>${esc(s.queue === "repro" ? t("queueRepro") : t("queueMain"))} #${s.no}${s.year ? " · " + s.year : ""}</span>${reason(s)}</li>`).join("");
  const noCode = C.no_official_code.map(s => `<li><b>${esc(s.name)}</b>${reason(s)}${s.url ? ` · ${out(s.url, t("paper"))}` : ""}</li>`).join("");
  const table = (cols, rows) => `<div class="table-scroll"><table class="census-table"><thead><tr>${cols}</tr></thead><tbody>${rows}</tbody></table></div>`;
  const stCols = `<th class="num">${esc(t("collected"))}</th><th class="num">${esc(t("pending"))}</th><th class="num">${esc(t("candidate"))}</th><th class="num">${esc(t("skipped"))}</th><th>${esc(t("bar"))}</th>`;
  main().innerHTML = `
  <header class="page-head"><h1>${esc(t("censusTitle"))}</h1><p>${esc(t("censusLede"))}</p></header>
  <section class="section" style="margin-top:0"><h2>${esc(t("amapTitle"))}</h2><p class="lede">${esc(t("amapLede"))}</p>${amapHtml(col)}</section>
  <section class="section"><h2>${esc(t("cDirTitle"))}</h2><p class="lede">${esc(t("cDirLede"))}</p>${legend}
    ${table(`<th>${esc(t("direction"))}</th>${stCols}`, dirRows)}</section>
  <section class="section"><h2>${esc(t("cFieldTitle"))}</h2><p class="lede">${esc(t("cFieldLede"))}</p>${legend}
    ${table(`<th>${esc(t("field"))}</th>${stCols}`, fieldRows)}</section>
  <section class="section"><h2>${esc(t("cSegTitle"))}</h2><p class="lede">${esc(t("cSegLede"))}</p>
    ${table(`<th>${esc(t("segment"))}</th>${stKeys.map(k => `<th class="num">${esc(qs(k))}</th>`).join("")}`, segRows)}
    <div style="margin-top:12px">${table(`<th>${esc(t("repro"))}</th>${rKeys.map(k => `<th class="num">${esc(qs(k))}</th>`).join("")}`, `<tr><td>${esc(t("queueRepro"))}</td>${rKeys.map(k => `<td class="num">${C.repro[k] || 0}</td>`).join("")}</tr>`)}</div></section>
  <section class="section"><h2>${esc(t("cMissTitle"))}</h2><p class="lede">${esc(t("cMissLede", col.length))}</p>
    ${table(`<th>${esc(t("field"))}</th><th class="num">${esc(t("count"))}</th><th class="num">%</th>`, missRows)}</section>
  <section class="section">
    <details class="reasons"><summary>${esc(t("cSkipTitle", C.skipped.length))}</summary><ul>${skip}</ul></details>
    <details class="reasons"><summary>${esc(t("cNoCodeTitle", C.no_official_code.length))}</summary><ul>${noCode}</ul></details>
  </section>`;
  wireAmap();
}

// ------------------------------------------------------------------ 关于
const SOURCE_EN = { "INDEX.md": "the library's master index of modules", "队列.md": "the main collecting queue", "队列-论文复现.md": "the queue of modules to rewrite from papers", "验证记录.md": "the test log", "扩队列记录.md": "the log of collecting rounds" };
function renderAbout() {
  // 关于页是馆长对来访者说的话。先讲这座馆和怎么逛，再讲每样东西的来历，最后才是怎么重新生成。
  const zh = !EN();
  const P = (z, e) => `<p>${zh ? z : e}</p>`;
  const H = (z, e) => `<h2>${zh ? z : e}</h2>`;
  const src = D.sources.map(s => zh ? `<li><code>${esc(s)}</code></li>` : `<li>${esc(SOURCE_EN[s.split("/").pop()] || "")}</li>`).join("");
  const def = ["author", "port", "repro", "third", "unknown"].map(k => `<dt><span class="src ${k}">${esc(t("srcName")[k])}</span></dt><dd>${esc(t("srcHint")[k])}</dd>`).join("");
  const n = D.exhibits.length, held = D.exhibits.filter(e => e.status === "collected").length;
  const reach = D.contact ? (/^https?:/.test(D.contact) ? `<a href="${esc(D.contact)}">${esc(D.contact)}</a>` : `<a href="mailto:${esc(D.contact)}">${esc(D.contact)}</a>`) : "";
  main().innerHTML = `<article class="prose">
  <header class="page-head"><h1>${esc(t("aboutTitle"))}</h1></header>
  ${P(`这是一份私人收藏。我想把注意力机制从 2014 年到今天出现过的模块收全，每一件都留下能运行的代码。馆里登记了 ${n} 件，其中 ${held} 件的代码已经收进来，其余的还在找或者准备照论文重写。`,
      `This is a private collection. I set out to gather every attention module that has appeared since 2014 and to keep runnable code for each. The museum lists ${n} of them. For ${held} the code is already here. The rest are still being tracked down or will be rewritten from the paper.`)}
  ${P("收藏不作商业用途。", "Nothing here is for commercial use.")}
  ${H("怎么逛", "Finding your way")}
  ${P("第一次来，从<a href=\"#/tour\">导览</a>开始。八个展室按年代讲这段历史，每一段文字旁边挂着它讲到的展品。想查某一件，去<a href=\"#/gallery\">展品</a>页搜名字，或者按领域翻。<a href=\"#/timeline\">时间线</a>把所有展品按年排开。<a href=\"#/graph\">关系图</a>有两种看法：总图把全馆摆在一张平面上，星团是可以转动的立体图。<a href=\"#/census\">统计</a>是账本。",
      "On a first visit, start with the <a href=\"#/tour\">tour</a>. Eight rooms tell the history in order, and each passage hangs beside the exhibits it mentions. To look up one piece, search the <a href=\"#/gallery\">objects</a> page by name or browse by field. The <a href=\"#/timeline\">timeline</a> lays everything out by year. The <a href=\"#/graph\">relations</a> page has two views: a flat map of the whole collection, and a constellation you can turn. <a href=\"#/census\">Numbers</a> is the ledger.")}
  ${H("展签上有什么", "What a label tells you")}
  ${P("最上面是论文里画这个模块的那张图，下面写着它是论文的第几张图，并链接到原文。然后是简介，对照论文摘要写的，讲它要解决什么问题、具体怎么算。再往下是前作和后作。最后是档案：论文、作者、代码仓库、许可证，以及这份代码和原版对照测试的结果。",
      "At the top is the figure from the paper that draws the module, with its figure number and a link to the source. Then a short overview, written from the paper's abstract: what problem the module addresses and how it computes. Then the pieces it built on and the pieces built on it. Last comes the record: paper, authors, code repository, licence, and how this copy of the code compared with the original in testing.")}
  ${P("哪一栏写着「缺」，就是我手里没有这一项的记录。我不替它补。", "A field marked “not recorded” means I hold no record of it. I do not fill it in.")}
  ${H("前作和后作怎么定", "How earlier and later versions are linked")}
  ${P("只连三种查得到依据的关系：名字里带版本号，而且前一版在馆里；论文题目点了另一件展品的名字；收集时的备注写明了它改自谁。名字只是普通英文词的、两件只是缩写相同的、同一篇论文里的两个模块，都不连。",
      "Only three kinds of link are drawn, each with written evidence: a version number in the name, with the earlier version held here; a paper title that names another exhibit; a collecting note that says what a piece was built on. Names that are ordinary English words, pieces that merely share an abbreviation, and two modules from one paper are left unlinked.")}
  ${P("总图里另有一种细线，是论文之间的引用，数据来自 OpenAlex。", "The map view also shows a thinner line for citations between papers, with data from OpenAlex.")}
  ${H("代码从哪来", "Where the code comes from")}<dl>${def}</dl>
  ${H("哪些代码能在这里看", "Which code you can read here")}
  ${P("只有我照论文自己写的那些，展签里可以直接展开。别人仓库里的代码留在我的库里，这里只给链接，因为其中不少仓库没有写明许可证。",
      "Only the pieces I wrote myself from the papers. Those open directly on the label. Code from other people's repositories stays in my library and appears here as a link, because many of those repositories state no licence.")}
  ${H("图和纹样的来历", "Where the pictures and ornaments come from")}
  ${P(`论文图取自各篇论文在 arXiv 上的页面，版权属于原作者。我把它们当作介绍这篇论文时的引用来放：每张图都写明是论文的第几张图，并链接到原文，尺寸只留到能看清结构。如果你是作者，不愿意自己的图出现在这里，${reach ? `请写信到 ${reach}，` : "请告诉我，"}我会撤下。`,
      `Paper figures come from each paper's page on arXiv and belong to their authors. I show them as quotations in the course of introducing each paper: every figure states its number in the paper and links to the source, and is kept only large enough to read the structure. If you are an author and would prefer your figure not to appear here, ${reach ? `write to ${reach} and` : "tell me and"} I will take it down.`)}
  ${P("首页的玫瑰窗和展签上的镶嵌画框是用代码按哥特花格的作图法算出来的。展室里画框四角的叶饰、展室末尾的花叶带和页脚的小花，出自 A. C. Pugin 的《哥特纹样》（1854 年版），已进入公有领域。左上角的馆徽是一张 4×4 的注意力权重图。下三角是每个位置能看到的位置，颜色深浅是权重。上三角的空格子是被因果掩码挡住的位置。",
      "The rose window on the home page and the inlaid frame on each label are computed in code from the geometry of Gothic tracery. The leaf corners on frames in the rooms, the foliage band that closes each room and the small rosette in the footer come from A. C. Pugin's Gothic Ornaments (1854 edition), now in the public domain. The emblem at the top left is a 4×4 map of attention weights. The lower triangle holds the positions each token can see, shaded by weight. The empty panes above it are the positions hidden by the causal mask.")}
  ${H("用到的开源组件", "Open-source components")}
  ${P("3d-force-graph 1.80.2（MIT）、three.js 0.187.0（MIT）用于星团。字体是 Archivo 和 IBM Plex Mono（SIL OFL 1.1）。它们都放在站内，页面不向别的网站请求任何东西。",
      "3d-force-graph 1.80.2 (MIT) and three.js 0.187.0 (MIT) draw the constellation. The fonts are Archivo and IBM Plex Mono (SIL OFL 1.1). All of them are served from this site, and the pages request nothing from anywhere else.")}
  ${H("许可", "Licence")}
  ${P("这个网站的代码按 MIT 许可开放。导览稿和每件展品的简介按 CC BY 4.0 开放，转载时请注明出处。论文图不在这两份许可里，它们属于各自的作者。",
      "The code of this site is released under the MIT licence. The tour text and the introduction to each exhibit are released under CC BY 4.0, so credit the museum when you reuse them. Paper figures are not covered by either licence. They belong to their authors.")}
  ${H("数据怎么来的", "How the data is built")}
  ${P("展品的记录由脚本从我的收藏库生成，不手写。来源是这几个文件，另加每个模块目录里的说明：", "The records are generated by script from my library and never typed by hand. The sources are these files, plus the notes kept in each module's folder:")}
  <ul>${src}</ul>
  <p class="muted">${zh ? "数据更新于 " : "Data last built "}${esc(D.generated)}</p>
  </article>`;
}

// ------------------------------------------------------------------ 展签
function row(k, v) { return v === null || v === undefined ? "" : `<dt>${esc(t(k))}</dt><dd>${v}</dd>`; }
function anchorsOf(id) {
  const res = [];
  chapters().forEach((c, i) => (c.anchors || []).forEach(a => { if (a.id === id) res.push({ c, i, a }); }));
  return res;
}
async function openObject(id) {
  const e = byId.get(id);
  const root = $("#drawer-root");
  if (!e) { root.innerHTML = ""; return; }
  const pu = paperUrl(e);
  const rel = D.edges.filter(g => g.target === id).map(g => ({ g, o: byId.get(g.source) }));
  const kids = D.edges.filter(g => g.source === id).map(g => ({ g, o: byId.get(g.target) }));
  const relHtml = (arr, label) => arr.length ? `<div class="rel-col"><h4>${esc(label)}</h4>${arr.map(({ g, o }) => `<a class="rel-item" href="#/x/${encodeURIComponent(o.id)}">${figBox(o, "mini")}<span><b>${esc(o.name_en)}</b> ${o.year || ""}<small>${esc(t("ruleLabel")[g.rule])}</small></span></a>`).join("")}</div>` : "";
  const halls = e.halls.map(h => `<a href="#/gallery?hall=${encodeURIComponent(hallKey(h))}">${esc(h.task ? hallName(h.field) + " · " + hallName(h.field, h.task) : hallName(h.field))}</a>`).join(EN() ? ", " : "、") || miss();
  const f = e.figure;
  const mech = mechHtml(e);
  const tours = anchorsOf(id).map(({ c, i, a }) => `<aside class="in-tour"><div class="in-tour-h">${esc(t("inTour"))} · ${esc(t("room", i + 1))} · ${esc(sx(c, "title"))}</div>${sx(a, "note") ? `<p>${esc(sx(a, "note"))}</p>` : ""}<a href="#/tour/${encodeURIComponent(c.id)}">${esc(t("backRoom", i + 1))} →</a></aside>`).join("");
  const copies = (e.copies || []).map(c => {
    const cl = fv(c, "license"), cv = fv(c, "verification");
    const cvs = EN() ? (c.en || {}).verification_source : c.verification_source;
    return `<div class="copy">
      <div><span class="src ${c.source_type}" title="${esc(t("srcHint")[c.source_type])}">${esc(t("srcName")[c.source_type])}</span>${txt(c, "name_en", "name") ? ` · <b>${esc(txt(c, "name_en", "name"))}</b>` : ""}</div>
      ${EN() ? "" : `<div class="path">${esc(c.path)}</div>`}
      <div>${esc(t("tRepo"))}: ${c.repo ? out(repoUrl(c), c.repo) : miss()}${c.commit ? ` · ${esc(t("commit"))} <code>${esc(c.commit.slice(0, 10))}</code>` : ""}${c.source_file_url ? ` · ${out(c.source_file_url, t("srcFile"))}` : ""}</div>
      ${cl === null ? "" : `<div>${esc(t("tLicense"))}: ${cl}</div>`}
      ${cv === null ? "" : `<div>${esc(t("tVerify"))}: ${cv}${c.verification && cvs ? ` <span class="muted">(${esc(t("verifyFrom", cvs))})</span>` : ""}</div>`}
    </div>`;
  }).join("");
  const queue = (e.queue || []).map(r => `<li>${esc(t("queueNo", r.queue === "repro" ? t("queueRepro") : t("queueMain"), r.no))} · ${esc(t("qSeg")[r.segment] || r.segment)} · ${esc(t("qStatus")[r.status] || r.status)}${r.note && !EN() ? `<br><span class="muted">${esc(r.note)}</span>` : ""}</li>`).join("");
  const reproCopies = (e.copies || []).filter(c => c.code_files);
  const licRow = e.source_type === "repro" && !e.license_note ? `<span class="muted">${esc(t("licRepro"))}</span>` : fv(e, "license_note", "license");
  const repoRow = e.repo ? out(repoUrl(e), e.repo) : (e.source_type === "repro" ? `<span class="muted">${esc(t("noRepo"))}</span>` : miss());
  const title = fv(e, "title");
  root.innerHTML = `<div class="drawer-back" data-close></div>
  <aside class="drawer" role="dialog" aria-modal="true" aria-labelledby="obj-name">
    <div class="drawer-bar"><span>${esc(t("tId"))} <code>${esc(e.id)}</code></span><button class="closer" type="button" data-close>${esc(t("close"))} ✕</button></div>
    <div class="drawer-body">
      <header class="obj-head">
        <div class="obj-year">${e.year || "?"}${txt(e, "venue") ? `<span>${esc(txt(e, "venue"))}</span>` : ""}</div>
        <h2 class="obj-name" id="obj-name">${esc(e.name_en)}</h2>
        ${zhName(e) ? `<div class="obj-zh">${esc(e.name_zh)}</div>` : ""}
        ${title ? `<div class="obj-title">${title}</div>` : ""}
      </header>
      <figure class="obj-fig">
        ${f ? `<a href="${esc(f.file)}" target="_blank" rel="noopener">${figBox(e, "big", true)}</a>` : figBox(e, "big")}
        ${f ? `<figcaption>${figCap(e)}${f.caption ? `<p class="fig-caption" lang="en">${esc(f.caption)}</p>` : ""}${figLicense(f.license) ? `<p class="fig-lic">${esc(t("figLic"))}: ${esc(figLicense(f.license))}</p>` : ""}<p class="fig-lic">${/publicdomain/.test(f.license || "") ? (EN() ? "Figure from the paper." : "图出自这篇论文。") : (EN() ? "Figure from the paper. Copyright belongs to its authors." : "图出自这篇论文，版权归原作者。")}</p></figcaption>` : ""}
      </figure>
      ${mech ? `<div class="obj-mech"><p>${mech}</p></div>` : ""}
      <p class="obj-links">${pu ? out(pu, t("tPaper")) : ""}${e.repo ? out(repoUrl(e), t("tRepo")) : ""}</p>
      ${tours}
      ${(rel.length || kids.length) ? `<section class="obj-sec"><h3>${esc(t("relTitle"))}</h3><div class="rel">${relHtml(rel, t("parents"))}${relHtml(kids, t("children"))}</div></section>` : ""}
      <details class="archive"><summary>${esc(t("recTitle"))}</summary>
      <dl class="tomb">
        ${row("tPaper", pu ? out(pu, e.arxiv ? "arXiv " + e.arxiv : e.doi ? "DOI " + e.doi : t("paper")) : miss())}
        ${e.authors ? row("tAuthors", fv(e, "authors")) : ""}
        ${row("tYear", e.year ? String(e.year) : miss())}
        ${row("tVenue", fv(e, "venue"))}
        ${row(e.status === "collected" ? "tSource" : "tStatus", srcMark(e))}
        ${row("tRepo", repoRow)}
        ${row("tLicense", licRow)}
        ${e.status === "collected" ? row("tVerify", fv(e, "verification")) : ""}
        ${row("tHall", halls)}
        ${e.direction ? row("tDirection", `<a href="#/gallery?hall=d:${e.direction}">${esc(dirName(e.direction))}</a>`) : ""}
        ${e.module_type ? row("tType", fv(e, "module_type")) : ""}
        ${e.domain ? row("tDomain", fv(e, "domain")) : ""}
        ${e.guo ? row("tGuo", fv(e, "guo")) : ""}
        ${e.skip_reason && !EN() ? row("skipReason", esc(e.skip_reason)) : ""}
        ${e.planned_source_type ? row("plannedSrc", esc(t("srcName")[e.planned_source_type])) : ""}
      </dl>
      ${copies ? `<section class="obj-sec"><h3>${esc(t("copiesTitle", e.copies.length))}</h3>${copies}</section>` : ""}
      ${queue ? `<section class="obj-sec"><h3>${esc(t("queueTitle"))}</h3><ul class="queue-list">${queue}</ul></section>` : ""}
      </details>
      ${e.status === "collected" ? `<section class="obj-sec"><h3>${esc(t("codeTitle"))}</h3>${reproCopies.length ? `<p class="muted" style="margin:0 0 8px">${esc(t("codeRepro"))}</p><div id="code-slot" class="muted">…</div>` : `<p class="muted" style="margin:0">${esc(t("codeNone"))}</p>`}</section>` : ""}
    </div>
  </aside>`;
  root.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", closeObject));
  $(".closer", root).focus();
  if (reproCopies.length) {
    try {
      if (!CODE) CODE = await (await fetch("data/code.json")).json();
      const html = reproCopies.map(c => Object.entries(CODE[c.path] || {}).map(([fn, src]) => `<details class="codebox"><summary>${esc(fn)}</summary><pre><code>${esc(src)}</code></pre></details>`).join("")).join("");
      const slot = $("#code-slot"); if (slot) { slot.className = ""; slot.innerHTML = html; }
    } catch (err) { const slot = $("#code-slot"); if (slot) slot.textContent = String(err); }
  }
}
function closeObject() { location.hash = "#/" + baseRoute; }

// ------------------------------------------------------------------ 路由
function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  const [path, qs] = h.split("?");
  return { path, params: new URLSearchParams(qs || "") };
}
let lastBase = null;
function route(force) {
  const { path, params } = parseHash();
  if (path.startsWith("x/")) {
    const id = decodeURIComponent(path.slice(2));
    if (lastBase === null) renderBase(baseRoute);
    openObject(id);
    return;
  }
  $("#drawer-root").innerHTML = "";
  const full = path + (params.toString() ? "?" + params : "");
  if (force || full !== lastBase) { baseRoute = full; renderBase(full); }
}
function renderBase(full) {
  lastBase = full;
  const [path, qs] = full.split("?");
  const params = new URLSearchParams(qs || "");
  const [name, sub] = path.split("/");
  document.querySelectorAll(".nav a").forEach(a => a.toggleAttribute("aria-current", false));
  const cur = document.querySelector(`.nav a[data-route="${name}"]`); if (cur) cur.setAttribute("aria-current", "page");
  tip.hide();
  graphCleanup();
  const y = scrollY;
  const keepScroll = name === "gallery" && params.has("n");
  if (name === "tour") sub ? renderRoom(decodeURIComponent(sub)) : renderTourIndex();
  else if (name === "timeline") renderTimeline(params);
  else if (name === "gallery") renderGallery(params);
  else if (name === "lineage") { location.replace("#/tour"); return; }   // 谱系页 2026-11-25 撤下，旧链接送去导览
  else if (name === "graph") renderGraph();
  else if (name === "census") renderCensus();
  else if (name === "about") renderAbout();
  else renderFoyer();
  if (keepScroll) scrollTo(0, y);
  else if (name !== "gallery" || !document.activeElement || document.activeElement.id !== "q") scrollTo(0, 0);
  const q = $("#q"); if (q && document.activeElement !== q && params.has("q")) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
  const titles = { tour: t("nav.tour"), timeline: t("nav.timeline"), gallery: t("nav.gallery"), lineage: t("nav.lineage"), graph: t("nav.graph"), census: t("nav.census"), about: t("nav.about") };
  document.title = (titles[name] ? titles[name] + " · " : "") + t("brand");
}

// ------------------------------------------------------------------ 语言和主题
function applyChrome() {
  document.documentElement.lang = EN() ? "en" : "zh-CN";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-aria]").forEach(el => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
  $("#lang-btn").textContent = EN() ? "ZH" : "EN";
  $(".brand-zh").textContent = t("brand"); $(".brand-en").textContent = t("brandSub");
  const th = document.documentElement.getAttribute("data-theme") || "auto";
  $("#theme-label").textContent = t("theme_" + th);
  document.documentElement.style.setProperty("--tb", $(".topbar").offsetHeight + "px");
  if (D) $("#foot-text").textContent = t("footer", D.generated.replace("T", " ").slice(0, 16), D.exhibits.length);
}
$("#lang-btn").addEventListener("click", () => { lang = EN() ? "zh" : "en"; store.set("acm-lang", lang); applyChrome(); route(true); });
$("#theme-btn").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") || "auto";
  const next = { auto: "light", light: "dark", dark: "auto" }[cur];
  if (next === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", next);
  store.set("acm-theme", next); applyChrome();
});
window.addEventListener("resize", () => document.documentElement.style.setProperty("--tb", $(".topbar").offsetHeight + "px"));
document.addEventListener("keydown", ev => { if (ev.key === "Escape" && $("#drawer-root").innerHTML) closeObject(); });

// ------------------------------------------------------------------ 启动
(async function boot() {
  applyChrome();
  try {
    D = await (await fetch("data/museum.json")).json();
  } catch (err) {
    main().innerHTML = `<p class="loading">${esc(t("loadFail"))}</p>`;
    console.error(err);
    return;
  }
  byId = new Map(D.exhibits.map(e => [e.id, e]));
  applyChrome();
  window.addEventListener("hashchange", () => route(false));
  route(true);
})();
